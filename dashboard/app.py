"""Dash App."""

from datetime import datetime, timedelta
import os

import dash
from dash import html
import dash_bootstrap_components as dbc
from dash import Dash, Input, Output
from flask import request
import pandas as pd
from flask_cors import CORS
import plotly.express as px

import plotly.io as pio
import logging
from src.parser import match_job_from_description
from src.scheduler import start_scheduler
from src.setup import DATA_DIR, config, save_config
from src.utils import load_existing_profile

logging.basicConfig(level=logging.INFO)

start_scheduler()

pio.templates["custom"] = pio.templates["plotly_dark"]
pio.templates["custom"].layout.colorway = px.colors.qualitative.Prism
pio.templates.default = "custom"

TABLE_STYLE = {
    "style_table": {
        "overflowX": "auto",
        "width": "100%",
        "minWidth": "100%",
        "margin": "20px 0 20px",
    },
    "style_cell": {
        "maxWidth": "200px",
        "maxHeight": "200px",
    },
}

app = Dash(__name__,
           use_pages=True,
           pages_folder="pages",
           external_stylesheets=[dbc.themes.CYBORG,
                                 dbc.icons.BOOTSTRAP],
           suppress_callback_exceptions=True,
           external_scripts=["/assets/note_area.js",
                             "/assets/match_job_text_area.js"],

           )

app.layout = dbc.Container([
    dbc.NavbarSimple(
        brand=html.Span([
            html.Img(src="/assets/logo.svg", height="40px", className="me-2"),
            "job-board"
        ]),
        brand_href="/",
        children=[
            dbc.NavItem(dbc.NavLink("Overview", href="/")),
            dbc.NavItem(dbc.NavLink("Jobs", href="/jobs")),
            dbc.NavItem(dbc.NavLink("Job Tracker", href="/jobs-tracker")),
            dbc.NavItem(dbc.NavLink("Match Job", href="/match-job")),
            dbc.NavItem(dbc.NavLink("Criteria & Profile", href="/profile")),
        ],
        className="mb-4"
    ),
    dash.page_container
], fluid=True)


app.clientside_callback(
    """
    function() { return true; }
    """,
    Output("profile-dirty", "data", allow_duplicate=True),
    Input("years-experience-input", "value"),
    Input("current-position-input", "value"),
    Input("summary-input", "value"),
    prevent_initial_call=True
)

server = app.server
CORS(server)


@server.route("/api/last-sync", methods=["GET"])
def last_sync() -> tuple:
    value = config.last_sync or (datetime.now() - timedelta(days=2))
    return {"last_sync": value.strftime("%Y-%m-%dT%H:%M:%S.000Z")}


@server.route("/api/sync-jobs", methods=["POST"])
def sync_jobs() -> tuple:
    data_filepath = os.path.join(DATA_DIR, "jobs.csv")
    jobs = request.json
    logging.info("Job sync requested.")
    new_df = pd.DataFrame(jobs)
    new_df["status"] = "applied"
    new_df["created_at"] = pd.to_datetime(
        new_df["created_at"]).dt.tz_localize(None)
    new_df["applied_at"] = pd.to_datetime(
        new_df["applied_at"]).dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    new_df["posted_time"] = pd.to_datetime(
        new_df["posted_time"]).dt.strftime("%Y-%m-%d %H:%M:%S.%f")

    existing_ids = set()
    if os.path.exists(data_filepath):
        existing_df = pd.read_csv(data_filepath)
        existing_ids = set(existing_df["job_id"].astype(str).values)

    filtered = new_df[~new_df["job_id"].isin(existing_ids)]

    if os.path.exists(data_filepath):
        filtered = filtered.reindex(columns=existing_df.columns)

    added = len(filtered)
    if added:
        filtered.to_csv(
            data_filepath,
            mode="a",
            header=not os.path.exists(data_filepath),
            index=False
        )

    config.last_sync = str(datetime.now())
    save_config(config)
    logging.info("Job Sync done.")
    return {"status": "ok", "added": added,
            "skipped": len(jobs) - added}, 200


@server.route("/api/match-job", methods=["POST"])
def get_match() -> tuple:
    job_description = request.json
    logging.info("Match Job requested.")
    if not job_description:
        return {"status": "error", "message": "Empty job description"}, 400

    profile = load_existing_profile()
    if (profile is None or not any(
                profile.model_dump(exclude={"years_of_experience"}).values())):
        return {"status": "error",
                "message": "No profile found to match"}, 404
    try:
        result, summary = match_job_from_description(
            job_description=job_description,
            user_profile=profile)
        logging.info("Match job done.")
        return {
            "status": "ok",
            "job_summary": summary.job_summary,
            "relevance_score": result.relevance_score,
            "matching_skills": result.matching_skills,
            "missing_requirements": result.missing_requirements
        }, 200
    except Exception as e:
        return {"status": "error",
                "message": f"Matching failed: {e}"}, 500
