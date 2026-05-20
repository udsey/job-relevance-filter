"""Review"""
import ast
import logging
import os
from typing import Any, Generator

import dash
from dash import Input, Output, State, callback, html, dcc, no_update
import dash_bootstrap_components as dbc
import pandas as pd

from src.setup import DATA_DIR, config


dash.register_page(__name__, path="/review")

_jobs_df: pd.DataFrame | None = None
filepath = os.path.join(DATA_DIR, "jobs.csv")
job_generator = None


def get_jobs() -> pd.DataFrame:
    global _jobs_df
    if _jobs_df is None:
        if not os.path.exists(filepath):
            return None
        _jobs_df = pd.read_csv(filepath)
        for col in ["missing_requirements", "matching_skills"]:
            _jobs_df[col] = _jobs_df[col].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else []
    )
    return _jobs_df


def get_filtered_jobs() -> pd.DataFrame:
    df = get_jobs()
    if not df:
        return None
    return df.loc[
        (df.relevance_score >= config.relevance_threshold) &
        (~df.status.isin({"apply", "remove"}))
    ]

def invalidate_jobs() -> None:
    global _jobs_df
    _jobs_df = None


def mark_status(job_id, status) -> None:
    df = pd.read_csv(filepath)
    df.loc[df.job_id == job_id, "status"] = status
    df.to_csv(filepath, index=False)
    invalidate_jobs()


def get_job_generator(jobs) -> Generator:
    for _, row in jobs.iterrows():
        yield row


def layout() -> html.Div:
    global job_generator
    jobs = get_filtered_jobs()
    if not jobs:
        return get_no_jobs_card()
    job_generator = get_job_generator(jobs)
    first = next(job_generator)
    return html.Div([
        html.Div(get_job_card(first), id="job-card-container"),
        dcc.Store(id="job-id", data=first.job_id)
    ])


def get_job_card(row: dict) -> dbc.Card:
    job_id = int(row.job_id)
    matching = row.matching_skills or []
    missing = row.missing_requirements or []
    if isinstance(matching, str):
        matching = [s.strip() for s in matching.split(",") if s.strip()]
    if isinstance(missing, str):
        missing = [s.strip() for s in missing.split(",") if s.strip()]

    score = row.relevance_score
    score_color = "success" if score and score >= 0.7 else "warning"
    return dbc.Card([
        dbc.CardBody([
            # Header row
            dbc.Row([
                dbc.Col([
                    html.H5(row.job_title, className="mb-0"),
                    html.Small(f"{row.company} · {row.location}", className="text-muted"),
                ], xs=9),
                dbc.Col([
                    dbc.Badge(f"Score: {score}", color=score_color, className="float-end"),
                ], xs=3),
            ], className="mb-2"),

            # Meta row
            html.Div([
                dbc.Badge(row.seniority, color="light", text_color="dark", className="me-1"),
                dbc.Badge(row.employment_type, color="light", text_color="dark", className="me-1"),
                dbc.Badge("Easy Apply" if row.easy_apply else "External", color="info", className="me-1"),
            ], className="mb-2"),

            # Description preview
            html.P(
                (row.description or "")[:2000] + "...",
                className="small mb-2"
            ),

            # Skills
            dbc.Row([
                    html.Small("Matching:", className="text-success fw-bold"),
                    html.Div([dbc.Badge(
                        s, color="success",
                        className="me-1 mt-1") for s in matching]),
            ]),
            dbc.Row([
                    html.Small("Missing:", className="text-danger fw-bold"),
                    html.Div([dbc.Badge(
                        s, color="danger",
                        className="me-1 mt-1") for s in missing]),
                ]),

            # Buttons
            dbc.Col([
                dbc.Button([html.I(className="bi bi-trash")],
                           size="sm", className="remove-btn",
                    id="remove-btn"
                ),
                html.A(
                    dbc.Button([html.I(className="bi bi-linkedin"),
                                " Apply"],
                                className="apply-btn", id="apply-btn"),
                    href=row.job_url,
                    target="_blank"
                    ),
                dbc.Button([html.I(className="bi bi-skip-forward")],
                            size="sm", className="skip-btn", id="skip-btn"
                ),
            ]),
        ])
    ], className="mb-3 job-card")

def get_no_jobs_card() -> dbc.Card:
    return dbc.Card([
        dbc.CardBody(
            html.Div("No more jobs!")
        )
    ], className="no-jobs-card")


@callback(
    Output("job-card-container", "children", allow_duplicate=True),
    Output("job-id", "data", allow_duplicate=True),
    Input("skip-btn", "n_clicks"),
    State("job-id", "data"),
    prevent_initial_call=True
)
def on_skip(n_clicks, job_id) -> Any:
    if not n_clicks:
        return no_update
    mark_status(job_id, "skip")
    try:
        next_row = next(job_generator)
        return get_job_card(next_row), next_row.job_id
    except StopIteration:
        return get_no_jobs_card(), no_update


@callback(
    Output("job-card-container", "children", allow_duplicate=True),
    Output("job-id", "data", allow_duplicate=True),
    Input("remove-btn", "n_clicks"),
    State("job-id", "data"),
    prevent_initial_call=True
)
def on_remove(n_clicks, job_id) -> Any:
    if not n_clicks:
        return no_update
    logging.error(job_id)
    mark_status(job_id, "remove")
    try:
        next_row = next(job_generator)
        return get_job_card(next_row), next_row.job_id
    except StopIteration:
        return get_no_jobs_card(), no_update


@callback(
    Output("job-card-container", "children", allow_duplicate=True),
    Output("job-id", "data", allow_duplicate=True),
    Input("apply-btn", "n_clicks"),
    State("job-id", "data"),
    prevent_initial_call=True
)
def on_apply(n_clicks, job_id) -> Any:
    if not n_clicks:
        return no_update
    mark_status(job_id, "apply")
    try:
        next_row = next(job_generator)
        return get_job_card(next_row), next_row.job_id
    except StopIteration:
        return get_no_jobs_card(), no_update