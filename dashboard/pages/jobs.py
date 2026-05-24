"""Review"""
import ast
from datetime import datetime
import os
from typing import Any, Generator

import dash
from dash import Input, Output, State, callback, html, dcc, no_update
import dash_bootstrap_components as dbc
import pandas as pd

from src.setup import DATA_DIR, config


dash.register_page(__name__, path="/jobs")

filepath = os.path.join(DATA_DIR, "jobs.csv")
job_generator = None


def get_jobs() -> pd.DataFrame:
    if not os.path.exists(filepath):
        return None
    df = pd.read_csv(filepath)
    df.created_at = pd.to_datetime(df.created_at)
    for col in ["missing_requirements", "matching_skills"]:
        df[col] = df[col].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) else [])
    return df


def get_filtered_jobs() -> pd.DataFrame:
    df = get_jobs()
    if df is None or df.empty:
        return None
    status_priority = {"new": 1, "seen": 0}
    df["status_order"] = df["status"].map(status_priority)
    return df.loc[
        (df.relevance_score >= config.relevance_threshold) &
        (~df.status.isin({"applied", "removed"}))
        ].sort_values(by=[
            "status_order",
            "relevance_score", "confidence_level", "created_at"],
            ascending=False)


def mark_status(job_id, status) -> None:
    df = pd.read_csv(filepath)
    df.loc[df.job_id == job_id, "status"] = status
    tracking_cols = ["applied_at", "screened_at",
                     "interview_at", "offered_at", "rejected_at", "notes"]
    for col in tracking_cols:
        if col not in df.columns:
            df[col] = ""

    if status == 'applied':
        df.loc[df.job_id == job_id, "applied_at"] = str(datetime.now())

    df.to_csv(filepath, index=False)


def get_job_generator(jobs) -> Generator:
    for _, row in jobs.iterrows():
        yield row


def layout() -> html.Div:
    global job_generator
    jobs = get_filtered_jobs()
    if jobs is None or jobs.empty:
        return get_no_jobs_card()
    job_generator = get_job_generator(jobs)
    first = next(job_generator)
    return html.Div([
        html.Div(get_job_card(first),
                 id="job-card-container"),
        dcc.Store(id="job-id", data=first.job_id)
    ])


def get_job_card(row: dict) -> dbc.Card:
    matching = row.matching_skills or []
    missing = row.missing_requirements or []
    if isinstance(matching, str):
        matching = [s.strip() for s in matching.split(",") if s.strip()]
    if isinstance(missing, str):
        missing = [s.strip() for s in missing.split(",") if s.strip()]

    score = row.relevance_score
    score_color = "info" if score and score >= 0.7 else "warning"
    return dbc.Card([
        dbc.CardBody([
            # Header row
            dbc.Row([
                dbc.Col([
                    html.H5(row.job_title, className="mb-0"),
                    html.Small(f"{row.company} · {row.location}",
                               className="text-muted"),
                ], xs=9),
                dbc.Col([
                    dbc.Badge(f"Score: {score}", color=score_color,
                              className="float-end"),
                ], xs=3),
            ], className="mb-2"),

            # Meta row
            html.Div([
                dbc.Badge(row.seniority,
                          color="light",
                          text_color="dark",
                          className="me-1"),
                dbc.Badge(row.employment_type,
                          color="light",
                          text_color="dark",
                          className="me-1"),
                dbc.Badge("Easy Apply" if row.easy_apply
                          else "External", color="info", className="me-1"),
            ], className="mb-2"),

            # Job summary
            html.P(
                row.job_summary or "",
                className="small mb-2"
            ),

            # Skills
            dbc.Row([
                    html.Big("Matching:"),
                    html.Div([dbc.Badge(
                        s, color="info", style={"fontWeight": "600"},
                        className="me-1 mt-1") for s in matching]),]),
            dbc.Row([
                    html.Big("Missing:"),
                    html.Div([dbc.Badge(
                        s, color="info", style={"fontWeight": "600"},
                        className="me-1 mt-1") for s in missing]),]),
        ]),
        dbc.CardFooter([
            dbc.Button([html.I(className="bi bi-trash")],
                       size="sm",
                       className="remove-btn",
                       id="remove-btn"),
            html.A(
                dbc.Button([
                    html.I(className="bi bi-linkedin"),
                    " Apply"],
                    className="apply-btn", id="apply-btn", color="info"),
                href=row.job_url,
                target="_blank",
                style={"display": "flex", "textDecoration": "none"}
                ),
            dbc.Button([html.I(className="bi bi-skip-forward")],
                       size="sm", className="skip-btn", id="skip-btn"),
        ])
    ])


def get_no_jobs_card() -> dbc.Card:
    return dbc.Card([
        dbc.CardBody([
            html.H2("No more jobs", className="card-text"),
            dbc.CardImg(src="/static/images/no_more_jobs.jpg", bottom=True),
            ])
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
    mark_status(job_id, "seen")
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
    mark_status(job_id, "removed")
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
    mark_status(job_id, "applied")
    try:
        next_row = next(job_generator)
        return get_job_card(next_row), next_row.job_id
    except StopIteration:
        return get_no_jobs_card(), no_update
