"""Dash App."""

import dash
from dash import html
import dash_bootstrap_components as dbc
from dash import Dash, Input, Output

import plotly.io as pio

# from src.scheduler import start_scheduler
# start_scheduler()

pio.templates["custom"] = pio.templates["plotly_white"]
pio.templates["custom"].layout.colorway = [
    "rgba(44, 22, 141, 0.5)", "#e2a49d", "#d4c0a0", "#9ca4d3"
]

pio.templates.default = "custom"

TABLE_STYLE = {
    "style_table": {
        "overflowX": "auto",
        "width": "100%",
        "minWidth": "100%",
    },
    "style_cell": {
        "maxWidth": "200px",
    },
}

app = Dash(__name__,
           use_pages=True,
           pages_folder="pages",
           external_stylesheets=[dbc.themes.BOOTSTRAP,
                                 dbc.icons.BOOTSTRAP],
           suppress_callback_exceptions=True,
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
            dbc.NavItem(dbc.NavLink("Jobs Tracking", href="/tracking")),
            dbc.NavItem(dbc.NavLink("Profile",
                                    href="/profile")),
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
