"""Overview."""
from datetime import datetime
import os
from typing import Any

import dash
from dash import ALL, Input, Output, State, callback, ctx, html, no_update
from dash import dcc
from dash import dash_table
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from dashboard.app import TABLE_STYLE
from dashboard.components.utils import rgb_to_rgba
from src.setup import DATA_DIR, config
import plotly.io as pio
from dashboard.components.kpi import kpi_card

PATH = "/tracking"
dash.register_page(__name__, path=PATH)

filepath = os.path.join(DATA_DIR, "jobs.csv")
STAGES = ["applied", "screened", "interview", "offered"]

STAGE_COL = {
    "applied": "applied_at",
    "screened": "screened_at",
    "interview": "interview_at",
    "offered": "offered_at",
}


def update_csv(job_id, col, value: str) -> None:
    df = pd.read_csv(filepath)
    df = df.astype({col: str})
    df.loc[df.job_id == int(job_id), col] = value
    df.to_csv(filepath, index=False)


def read_jobs_csv() -> pd.DataFrame | None:
    if not os.path.exists(filepath):
        return None
    df = pd.read_csv(filepath)
    if df.empty:
        return None
    at_cols = [c for c in df.columns if c.endswith("_at")]
    df[at_cols] = df[at_cols].apply(pd.to_datetime)
    df["response_status"] = df.apply(get_status, axis=1)
    return df[df.status == "applied"]


def get_kpi_dict(df: pd.DataFrame):
    applied = df[df.status == "applied"]
    total_applied = applied.shape[0]
    responded = applied["screened_at"].notna().sum()
    interviewed = applied["interview_at"].notna().sum()

    days_to_response = (
        pd.to_datetime(applied["screened_at"]) -
        pd.to_datetime(applied["applied_at"])
    ).dt.days.dropna()

    avg_days_to_response = (days_to_response.mean()
                            if not days_to_response.empty
                            else 0)

    return {
        "applied": total_applied,
        "response_rate": responded / (total_applied or 1e-6),
        "interview_rate": interviewed / (total_applied or 1e-6),
        "avg_days_to_response": avg_days_to_response
    }


def get_status(row) -> str:
    if pd.notna(row["rejected_at"]):
        return "rejected"
    if pd.notna(row["offered_at"]):
        return "offered"
    if pd.notna(row["interview_at"]):
        days = (
            pd.Timestamp.today() - pd.to_datetime(row["interview_at"])).days
        return (
            "no_response" if days >= config.no_response_days else "interview")
    if pd.notna(row["screened_at"]):
        days = (pd.Timestamp.today() - pd.to_datetime(row["screened_at"])).days
        return (
            "no_response" if days >= config.no_response_days else "screened")
    if pd.notna(row["applied_at"]):
        days = (pd.Timestamp.today() - pd.to_datetime(row["applied_at"])).days
        return (
            "no_response" if days >= config.no_response_days else "applied")
    return "no_response"


def get_job_table(df) -> pd.DataFrame:
    jobs = df[["job_id", "job_title", "company", "location",
               "applied_at", "job_url", "notes"]]
    jobs["response_status"] = df.apply(get_status, axis=1)
    return jobs[["job_id", "job_title", "company", "location", "job_url",
                 "applied_at", "response_status", "notes"]]


def layout() -> html.Div:
    df = read_jobs_csv()
    if df is None or df.empty:
        return get_no_applications_card()

    job_table = get_job_table(df)
    kpis = get_kpi_dict(df)

    return html.Div([
        get_kpis(kpis),
        get_sankey(df),
        get_kanban(job_table),
        get_table(job_table),
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle(id="notes-modal-title")),
            dbc.ModalBody(
                dcc.Textarea(id="note-textarea"))
        ], id="kanban-notes-modal"),
        dcc.Store(id="notes-store"),
        dcc.Store(id="add-job-stage-store"),
        dcc.Location(id="page-location", refresh=True),
        dbc.Modal([
            dbc.ModalHeader("Add Job"),
            dbc.ModalBody([
                dbc.Input(id="add-job-title", placeholder="Job Title"),
                dbc.Input(id="add-job-company", placeholder="Company"),
                dbc.Input(id="add-job-url", placeholder="URL"),
                dbc.Input(id="add-job-location", placeholder="Location"),
                dbc.Textarea(id="add-job-notes",
                             placeholder="Notes (optional)"),
            ]),
        ], id="add-job-modal"),
            ])


def get_no_applications_card() -> dbc.Card:
    return dbc.Card([
        dbc.CardBody([
            html.H2("You haven't applied to any jobs yet",
                    className="card-text"),
            dbc.CardImg(src="assets/no_applications.jpg", bottom=True),
            ])
    ], className="no-jobs-card")


def get_table(df: pd.DataFrame) -> html.Div:
    df["job_url"] = df["job_url"].apply(
        lambda x: f"[link]({x})" if pd.notna(x) else "")
    df = df[df.response_status != "rejected"]
    return html.Div(
                    dash_table.DataTable(
                        id="job-aplication-table",
                        data=df.to_dict("records"),
                        columns=[
                            {"name": c, "id": c, "presentation": "markdown"}
                            if c == "job_url" else {"name": c, "id": c}
                            for c in df.columns
                        ],
                        page_size=20,
                        sort_action="native",
                        filter_action="native",
                        markdown_options={"link_target": "_blank"},
                        **TABLE_STYLE
                    ),
                    id="table-container",)


def get_kpis(kpis: dict) -> html.Div:
    return html.Div([
        dbc.Row([
            kpi_card("Total Applied", kpis["applied"]),
            kpi_card("Response Rate", f"{kpis['response_rate']:.0%}"),
            kpi_card("Interview Rate", f"{kpis['interview_rate']:.0%}"),
            kpi_card(
                "Average days to response",
                f"{kpis['avg_days_to_response']:.0%}"),
        ]),
        ], className="kpi-body")


def get_sankey(df: pd.DataFrame) -> dcc.Graph:
    labels = ["Applied", "Screening", "Interview",
              "Offered", "Rejected", "No Response"]
    idx = {le: i for i, le in enumerate(labels)}

    sources, targets, values = [], [], []

    def add(src, tgt, count) -> None:
        if count > 0:
            sources.append(idx[src])
            targets.append(idx[tgt])
            values.append(count)

    screened = df["screened_at"].notna()
    interviewed = df["interview_at"].notna()
    offered = df["offered_at"].notna()
    rejected = df["rejected_at"].notna()

    add("Applied", "No Response", (~screened).sum())
    add("Applied", "Screening", screened.sum())
    add("Screening", "Interview", (screened & interviewed).sum())
    add("Screening", "Rejected", (screened & rejected & ~interviewed).sum())
    add("Interview", "Offered", (interviewed & offered).sum())
    add("Interview", "Rejected", (interviewed & rejected & ~offered).sum())
    add("Offered", "Rejected", (offered & rejected).sum())
    colors = pio.templates["custom"].layout.colorway
    node_colors = [rgb_to_rgba(c, alpha=0.4) for c in colors[:len(labels)]]

    fig = go.Figure(go.Sankey(
        node=dict(label=labels,
                  pad=40,
                  thickness=10,
                  color=colors),
        link=dict(source=sources,
                  target=targets,
                  value=values,
                  color=node_colors)
    ))
    fig.update_layout(title="Application Funnel")
    return dcc.Graph(figure=fig)


def get_kanban(df: pd.DataFrame) -> html.Div:
    return html.Div([
        dbc.Row([
            dbc.Card([
                dbc.CardHeader(stage.capitalize()),
                dbc.CardBody([
                    get_kanban_card(row)
                    for _, row in df[df.response_status == stage].iterrows()
                ], id=f"kanban-{stage}"),
                dbc.CardFooter(
                    dbc.Button(html.I(className="bi bi-plus"),
                               size="sm",
                               className="kanban-add-btn",
                               id={"type": "kanban-add", "index": stage}),
                ),
            ], className="kanban-card") for stage in STAGES
        ]),
    ], className="kanban-body", id="kanban-container")


def get_kanban_card(row) -> dbc.Card:
    return dbc.Card([
        dbc.CardHeader([
            html.Small(row.job_title),
            dbc.Button(
                html.I(className="bi bi-journal-text"),
                size="sm",
                style={"fontSize": "20px"},
                className="kanban-note-btn",
                id={"type": "kanban-note", "index": str(row.job_id)})]),
        dbc.CardBody([
            html.Small([
                row.company, " · ",
                html.A("link", href=row.job_url, target="_blank",
                       style={"textDecoration": "none"})
            ], className="text-muted"),
        ]),
        dbc.CardFooter([
            dbc.Button(html.I(className="bi bi-arrow-left"),
                       size="sm", className="kanban-btn",
                       id={"type": "kanban-prev", "index": str(row.job_id)}),
            dbc.Button(html.I(className="bi bi-x"),
                       size="sm",
                       className="kanban-btn-reject",
                       id={"type": "kanban-reject", "index": str(row.job_id)}),
            dbc.Button(html.I(className="bi bi-arrow-right"),
                       size="sm",
                       className="kanban-btn",
                       id={"type": "kanban-next", "index": str(row.job_id)}),
        ])
    ], className="kanban-element",
       id={"type": "kanban-element", "index": str(row.job_id)})


@callback(
    Output("tr-cell-modal", "is_open"),
    Output("tr-cell-modal-body", "children"),
    Input("job-aplication-table", "active_cell"),
    State("job-aplication-table", "derived_virtual_data"),
)
def show_cell(active_cell, data) -> tuple:
    if not active_cell or not data:
        return False, None
    value = data[active_cell["row"]][active_cell["column_id"]]
    return True, str(value)


@callback(
    Output("page-location", "href", allow_duplicate=True),
    Input({"type": "kanban-reject", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def on_kanban_reject_action(n_clicks) -> Any:
    if not any(n_clicks):
        return no_update
    triggered = ctx.triggered_id
    if not triggered:
        return no_update
    job_id = triggered["index"]
    update_csv(job_id, "rejected_at", str(datetime.now()))
    return PATH


@callback(
    Output("kanban-container", "children"),
    Input({"type": "kanban-next", "index": ALL}, "n_clicks"),
    Input({"type": "kanban-prev", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def on_kanban_nav_action(next_clicks, prev_clicks) -> Any:
    if not any(next_clicks + prev_clicks):
        return no_update

    triggered = ctx.triggered_id
    if not triggered:
        return no_update

    job_id = triggered["index"]
    action = triggered["type"]

    applied_df = read_jobs_csv()
    row = applied_df[applied_df.job_id == int(job_id)].iloc[0]
    current_status = get_status(row)

    if action == "kanban-next":
        idx = STAGES.index(current_status)
        if idx < len(STAGES) - 1:
            next_stage = STAGES[idx + 1]
            update_csv(job_id, STAGE_COL[next_stage], str(datetime.now()))

    elif action == "kanban-prev":
        idx = STAGES.index(current_status)
        if idx > 0:
            update_csv(job_id, STAGE_COL[current_status], None)

    df = read_jobs_csv()
    job_table = get_job_table(df)
    return get_kanban(job_table).children


@callback(
    Output("kanban-notes-modal", "is_open"),
    Output("notes-modal-title", "children"),
    Output("note-textarea", "value"),
    Output("notes-store", "data"),
    Input({"type": "kanban-note", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def on_kanban_note(note_clicks) -> tuple:
    if not any(note_clicks):
        return no_update, no_update, no_update, no_update
    triggered = ctx.triggered_id
    if not triggered:
        return no_update, no_update, no_update, no_update
    job_id = triggered["index"]
    df = read_jobs_csv()
    row = df[df.job_id == int(job_id)].iloc[0]
    title = f"{row.job_title} · {row.company}"
    notes = str(row.notes) if pd.notna(row.notes) else ""
    return True, title, notes, job_id


@callback(
    Output("table-container", "children"),
    Input("kanban-notes-modal", "is_open"),
    State("notes-store", "data"),
    State("note-textarea", "value"),
    prevent_initial_call=True
)
def on_notes_close(is_open, job_id, notes) -> Any:
    if is_open or not job_id:
        return no_update
    update_csv(job_id, "notes", notes)
    job_table = get_job_table(read_jobs_csv())
    return get_table(job_table)


@callback(
    Output("add-job-modal", "is_open"),
    Output("add-job-stage-store", "data"),
    Input({"type": "kanban-add", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def on_add_job(n_clicks) -> Any:
    if not any(n_clicks):
        return no_update, no_update
    triggered = ctx.triggered_id
    if not triggered:
        return no_update, no_update
    return True, triggered["index"]


@callback(
    Output("page-location", "href", allow_duplicate=True),
    Input("add-job-modal", "is_open"),
    State("add-job-stage-store", "data"),
    State("add-job-title", "value"),
    State("add-job-company", "value"),
    State("add-job-url", "value"),
    State("add-job-location", "value"),
    State("add-job-notes", "value"),
    prevent_initial_call=True
)
def on_add_job_close(is_open, stage, title,
                     company, url, location, notes) -> tuple:
    if is_open or not stage or not title:
        return no_update

    job_id = int(datetime.now().timestamp() * 1000)
    now = str(datetime.now())

    new_row = {
        "job_id": job_id,
        "job_title": title,
        "company": company,
        "job_url": url,
        "location": location,
        "notes": notes,
        "status": "applied",
    }
    for s in STAGES:
        new_row[STAGE_COL[s]] = (
            now if STAGES.index(s) <= STAGES.index(stage) else None)

    df = pd.read_csv(filepath)
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(filepath, index=False)
    return PATH
