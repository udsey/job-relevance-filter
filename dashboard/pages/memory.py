"""Memory."""
from datetime import datetime
import os

import dash
from dash import Input, Output, State, callback, html, no_update
from croniter import croniter
from dash import dcc
from dash import dash_table
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px
from src.scheduler import scheduler
from apscheduler.triggers.date import DateTrigger
from src.run import run
from dashboard.styles import TABLE_STYLE
from src.setup import CONFIG_DIR, DATA_DIR, config, load_config
from src.utils import load_existing_criteria, load_existing_profile
from src.memory import memory_store
from dashboard.components.kpi import kpi_card
from src.models import AddEntryModel, MemoryEntryModel

PATH = "/memory"
dash.register_page(__name__, path=PATH)

def layout() -> html.Div:
    if memory_store.is_empty:
        return get_empty_page()

    metadata = memory_store.get_metadata()
    categories = list({entry.category for entry in metadata
                       if not entry.is_deleted})
    kpi_dict = get_kpi_dict(metadata)
    data, columns = get_table_data(metadata)

    return html.Div([
        get_kpis(kpi_dict),
        get_toolbar(categories),
        get_table(data, columns),
        dcc.Location(id="url")
    ])


def get_empty_page() -> html.Div:
    text = html.Div([
        html.P(["Your memory is empty. Upload your CV on the ",
                dcc.Link("Profile page", href="/profile"),
                " to get started.",
                ]),
        html.P([
            "You can also save entries directly using the ",
            dcc.Link(
                "Firefox extension",
                href="https://github.com/udsey/linkedin-extension/tree/main")
                ]),
        ])
    return html.Div([
        html.H3("No memory yet..."),
        dbc.Card([
            dbc.CardBody(text),
            dbc.CardImg(src="/static/images/empty_memory.jpg", bottom=True),
        ])
    ])


def get_kpi_dict(metadata: list[MemoryEntryModel]) -> dict:
    active = [e for e in metadata if not e.is_deleted]
    return {
        "total_entries": len(active),
        "total_categories": len(set(e.category for e in active)),
        "profile_entries": len([e for e in active if e.source == "profile"]),
        "manual_entries": len([e for e in active if e.source == "manual"]),
    }


def get_kpis(kpi_dict: dict) -> html.Div:
    return html.Div([
        dbc.Row([
            kpi_card("Total Entries", kpi_dict["total_entries"]),
            kpi_card("Total Categories", kpi_dict["total_categories"]),
            kpi_card("Profile Entries", kpi_dict["profile_entries"]),
            kpi_card("Manual Entries", kpi_dict["manual_entries"]),
        ])
        ], className="kpi-body")


def get_table_data(metadata: list[MemoryEntryModel]) -> tuple:
    skip = ["score"]
    data = sorted(
        [e.model_dump() for e in metadata],
        key=lambda x: x["is_deleted"]
    )

    columns = [
        {"name": col, "id": col}
        for col in MemoryEntryModel.model_fields
        if col not in skip
    ]

    columns = [{"name": "action", "id": "action"}] + columns

    for row in data:
        row["created_at"] = row["created_at"].replace("T", " ").split(".")[0]
        row["action"] = "🗑️ Delete" if not row["is_deleted"] else "↩️ Restore"
    return data, columns



def get_table(data: dict, columns: dict) -> dash_table.DataTable:
    return dash_table.DataTable(
        id="memory-table",
        data=data,
        columns=columns,
        page_size=20,
        sort_action="native",
        filter_action="native",
        derived_virtual_data=[],
        style_table=TABLE_STYLE["style_table"],
        style_cell=TABLE_STYLE["style_cell"],
        style_data_conditional=[{
            "if": {"column_id": "action"},
            "cursor": "pointer",
        }]
    )


def get_toolbar(categories: list[str]) -> dbc.Row:
    return dbc.Row([
        dbc.Col(dbc.Button([
            html.I(className="bi bi-trash3 me-2"),
            "Wipe All"
        ], id="memory-wipe-btn", color="danger", size="sm"), width="auto"),

        dbc.Col(dbc.InputGroup([
            dbc.Select(
                id="memory-category-select",
                options=[{"label": c, "value": c} for c in categories],
                placeholder="Select category...",
            ),
            dbc.Button([
                html.I(className="bi bi-trash me-2"),
            ],
            id="memory-delete-category-btn",
            color="warning",
            title="Delete Category")
        ]), width="auto"),

        dbc.Col(
            dbc.InputGroup([
                    dbc.Input(id="memory-add-category",
                              placeholder="Category..."),
                    dbc.Input(id="memory-add-content",
                              placeholder="Content..."),
                    dbc.Button(html.I(className="bi bi-plus-lg me-2"),
                                title="Add Entry",
                                id="memory-add-btn",
                                color="primary")
            ]), width=True)
    ], className="mb-3 g-2 align-items-center", id="memory-toolbar")


@callback(
    Output("memory-table", "data"),
    Output("memory-table", "active_cell"),
    Input("memory-table", "active_cell"),
    State("memory-table", "derived_virtual_data"),
    prevent_initial_call=True
)
def handle_memory_action(active_cell, data) -> tuple:
    if not active_cell or active_cell["column_id"] != "action":
        return no_update, None

    row = data[active_cell["row"]]
    print(row["is_deleted"])
    print(row["id"])

    if row["is_deleted"]:
        memory_store.restore_entry(row["id"])
    else:
        memory_store.delete_entry(row["id"])

    metadata = memory_store.get_metadata()
    data, _ = get_table_data(metadata)
    return data, None


@callback(
    Output("url", "href", allow_duplicate=True),
    Input("memory-wipe-btn", "n_clicks"),
    prevent_initial_call=True
)
def handle_wipe(n_clicks) -> list:
    if not n_clicks:
        return no_update
    memory_store.wipe()
    return PATH


@callback(
    Output("url", "href", allow_duplicate=True),
    Input("memory-delete-category-btn", "n_clicks"),
    State("memory-category-select", "value"),
    prevent_initial_call=True
)
def handle_delete_category(n_clicks, category) -> dict:
    if not n_clicks or not category:
        return no_update
    memory_store.delete_category(category)
    return PATH


@callback(
    Output("url", "href", allow_duplicate=True),
    Input("memory-add-btn", "n_clicks"),
    State("memory-add-category", "value"),
    State("memory-add-content", "value"),
    prevent_initial_call=True
)
def handle_add_entry(n_clicks, category, content) -> dict:
    if not n_clicks or not category or not content:
        return no_update
    memory_store.add_entry(AddEntryModel(category=category,
                                         content=content))
    return PATH
