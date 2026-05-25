"""Dash App."""

import dash
from dash import html
import dash_bootstrap_components as dbc
from dash import Dash
from flask_cors import CORS
from dashboard.callbacks import init_callbacks

import logging
from src.scheduler import start_scheduler
from dashboard.endpoints import blueprint

logging.basicConfig(level=logging.INFO)

start_scheduler()

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
            dbc.NavItem(dbc.NavLink("Memory", href="/memory"))
        ],
        className="mb-4"
    ),
    dash.page_container
], fluid=True)

init_callbacks(app)

server = app.server
server.register_blueprint(blueprint)
CORS(server)
