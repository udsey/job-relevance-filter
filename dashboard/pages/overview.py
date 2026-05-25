"""Overview."""
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
from dashboard.components.kpi import kpi_card


dash.register_page(__name__, path="/")

filepath = os.path.join(DATA_DIR, "jobs.csv")


def read_jobs_csv() -> pd.DataFrame | None:
    if not os.path.exists(filepath):
        return None
    df = pd.read_csv(filepath)
    if df.empty:
        return None
    df.created_at = pd.to_datetime(df.created_at)
    return df


def get_kpi_dict(df: pd.DataFrame):
    total_found = df.shape[0]
    pending = df[(df.status == "new") &
                 (df.relevance_score >= config.relevance_threshold)].shape[0]
    rejected = df[df.status == "removed"].shape[0]
    applied = df[df.status == "applied"].shape[0]
    seen = df[df.status == "seen"].shape[0]
    reviewed = rejected + applied + seen
    return {
        "total": df.shape[0],
        "total_today": df[
            df.created_at.dt.date == pd.Timestamp.today().date()].shape[0],
        "applied": applied,
        "pending": pending,
        "rejected": rejected,
        "seen": seen,
        "reviewed": reviewed,
        "apply_rate": applied / (reviewed or 1e-6),
        "reject_rate": rejected / (total_found or 1e-6),
        "average_relevance_score": df.relevance_score.mean(),
        "average_relevance_score_rejected": df.loc[
            df.status == "removed", "relevance_score"].mean(),
        "average_relevance_score_applied": df.loc[
            df.status == "applied", "relevance_score"].mean(),
        "average_relevance_score_pending": df.loc[
            df.status == "new", "relevance_score"].mean()
    }


def get_chart_data(df: pd.DataFrame) -> dict:
    return {
        "relevance_scores": df.relevance_score.dropna().tolist(),
        "status_counts": df.status.value_counts().to_dict(),
        "seniority_counts": df.seniority.value_counts().to_dict(),
        "employment_type_counts": df.employment_type.value_counts().to_dict(),
        "easy_apply_counts": df.easy_apply.value_counts().to_dict(),
        "top_companies": df.company.value_counts()[:10].to_dict(),
        "daily_stats": (
            df.groupby([df.created_at.dt.floor("h"), "status"])
            .size()
            .unstack(fill_value=0)
            .reset_index()
            .rename(columns={"created_at": "date"})
            .to_dict(orient="list"))
    }


def layout() -> html.Div:
    df = read_jobs_csv()
    if df is None or df.empty:
        return get_empty_page()

    kpis = get_kpi_dict(df)
    chart_data = get_chart_data(df)

    return html.Div([
        get_run_panel(),
        get_kpis(kpis),
        get_charts(chart_data),
        get_table(df),
        dcc.Store(id="run-started-store"),
        dcc.Interval(id="run-poll-interval", interval=2000, disabled=True),
        dbc.Modal([dbc.ModalBody(id="cell-modal-body"),], id="cell-modal"),
    ])


def get_empty_page() -> html.Div:
    setups = set()
    if (not os.path.exists(os.path.join(CONFIG_DIR, "criteria.yaml"))
            or not load_existing_criteria()):
        setups.add("criteria")

    if not os.path.exists(os.path.join(CONFIG_DIR, "profile.yaml")):
        setups.add("profile")
    else:
        profile = load_existing_profile()
        if (
            profile is None or not any(
                profile.model_dump(exclude={"years_of_experience"}).values())):
            setups.add("profile")

    if setups:
        missing = ", ".join(sorted(setups))
        text = html.Div([
            html.P(
                f"Please complete the following setup(s): {missing}."
            ),
            html.P([
                "Go to the ",
                dcc.Link("Profile page", href="/profile"),
                " to configure them.",
            ]),
        ])
    else:
        cron_expr = config.cron.replace(" ", "+")
        text = html.Div([
            html.P(
                "Your next job search is scheduled to run "
                "according to your cron schedule:"
            ),
            html.P([
                html.Code(config.cron),
            ]),
            html.P([
                html.A(
                    "Explain this schedule on crontab.guru",
                    href=f"https://crontab.guru/#{cron_expr}",
                    target="_blank",
                ),
            ]),
        ])
    return html.Div([
        html.H3("No jobs found yet"),
        dbc.Card([
            dbc.CardBody(text),
            dbc.CardImg(src="/static/images/empty_overview.jpg", bottom=True),
        ])
    ])


def get_table(df) -> dash_table:
    return dash_table.DataTable(
                    id="job-table",
                    data=df.to_dict("records"),
                    columns=[
                        {"name": c, "id": c, "presentation": "markdown"}
                        if c == "job_id" else {"name": c, "id": c}
                        for c in df.columns
                    ],
                    page_size=20,
                    sort_action="native",
                    filter_action="native",
                    **TABLE_STYLE
                )


def get_run_panel() -> html.Div:
    config = load_config()
    if config.last_run:
        last_run_text = config.last_run.strftime("%b %d, %Y %H:%M")
    else:
        last_run_text = "Never"

    next_run = croniter(config.cron, datetime.now()).get_next(datetime)
    hours_until = round((next_run - datetime.now()).total_seconds() / 3600, 1)

    return html.Div([
        html.Span(
            html.I(className="bi bi-clock-history"),
            className="run-panel-icon"
        ),
        html.Span(
            f"Last run: {last_run_text} · Next run in {hours_until} hours",
            id="run-last-run-text",
            className="run-panel-text"),
        dbc.Button(
            html.I(className="bi bi-play-fill", id="run-btn-icon"),
            id="run-now-btn",
            size="sm",
            className="run-panel-btn",
            title="Run now"
        ),
    ], className="run-panel")


def get_kpis(kpis) -> html.Div:
    return html.Div([
        dbc.Row([
            kpi_card("Total", kpis["total"]),
            kpi_card("Found Today", kpis["total_today"]),
            kpi_card("Apply Rate", f"{kpis['apply_rate']:.0%}"),
            kpi_card("Reject Rate", f"{kpis['reject_rate']:.0%}"),
        ]),
        dbc.Row([
                kpi_card("Pending", kpis["pending"]),
                kpi_card("Applied", kpis["applied"]),
                kpi_card("Rejected", kpis["rejected"]),
                kpi_card("Reviewed", kpis["reviewed"]),
                ]),
        dbc.Row([
            kpi_card(
                "Avg Score", f"{kpis['average_relevance_score']:.2f}"),
            kpi_card(
                "Avg Score Rejected",
                f"{kpis['average_relevance_score_rejected']:.2f}"),
            kpi_card(
                "Avg Score Applied",
                f"{kpis['average_relevance_score_applied']:.2f}"),
            kpi_card(
                "Avg Score Pending",
                f"{kpis['average_relevance_score_pending']:.2f}"),
        ]),
        ], className="kpi-body")


def get_charts(data: dict) -> html.Div:
    return html.Div([
        dbc.Row([
            dbc.Col(dcc.Graph(figure=px.line(
                data_frame=pd.DataFrame(data["daily_stats"]),
                x="date",
                y=[c for c in data["daily_stats"] if c != "date"],
                title="Jobs Over Time",
                labels={"value": "Count", "variable": "Status"},
                markers=True,
            )), md=12),
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=px.histogram(
                x=data["relevance_scores"],
                nbins=20,
                title="Relevance Score Distribution",
                labels={"x": "Score"}
            )), md=6),
            dbc.Col(dcc.Graph(figure=px.pie(
                names=list(data["status_counts"].keys()),
                values=list(data["status_counts"].values()),
                title="Status Breakdown"
            )), md=6),
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=px.bar(
                x=list(data["seniority_counts"].keys()),
                y=list(data["seniority_counts"].values()),
                title="Jobs by Seniority",
                labels={"x": "Seniority", "y": "Count"}
            )), md=6),
            dbc.Col(dcc.Graph(figure=px.bar(
                x=list(data["top_companies"].keys()),
                y=list(data["top_companies"].values()),
                title="Top Companies",
                labels={"x": "Company", "y": "Count"}
            )), md=6),
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=px.pie(
                names=list(data["employment_type_counts"].keys()),
                values=list(data["employment_type_counts"].values()),
                title="Employment Type"
            )), md=6),
            dbc.Col(dcc.Graph(figure=px.pie(
                names=["Easy Apply", "External"],
                values=[
                    data["easy_apply_counts"].get(True, 0),
                    data["easy_apply_counts"].get(False, 0)
                ],
                title="Easy Apply vs External"
            )), md=6),
        ]),
    ])


@callback(
    Output("cell-modal", "is_open"),
    Output("cell-modal-body", "children"),
    Input("job-table", "active_cell"),
    State("job-table", "derived_virtual_data"),
)
def show_cell(active_cell, data) -> tuple:
    if not active_cell or not data:
        return False, None
    value = data[active_cell["row"]][active_cell["column_id"]]
    return True, str(value)


@callback(
    Output("run-now-btn", "disabled"),
    Output("run-btn-icon", "className"),
    Output("run-poll-interval", "disabled"),
    Output("run-started-store", "data"),
    Input("run-now-btn", "n_clicks"),
    prevent_initial_call=True
)
def on_run_now(n_clicks) -> tuple:
    scheduler.add_job(run, DateTrigger(run_date=datetime.now()))
    current = load_config().last_run
    return True, "bi bi-arrow-repeat spin", False, str(current)


@callback(
    Output("run-now-btn", "disabled", allow_duplicate=True),
    Output("run-btn-icon", "className", allow_duplicate=True),
    Output("run-poll-interval", "disabled", allow_duplicate=True),
    Output("run-last-run-text", "children"),
    Input("run-poll-interval", "n_intervals"),
    State("run-started-store", "data"),
    prevent_initial_call=True
)
def poll_run_status(n_intervals, started_value) -> tuple:
    current = load_config().last_run
    if str(current) == started_value:
        return no_update, no_update, no_update, no_update

    last_run_text = (current.strftime("%b %d, %Y %H:%M")
                     if current else "Never")
    return False, "bi bi-play-fill", True, f"Last run: {last_run_text}"
