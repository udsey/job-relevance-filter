"""Dash App."""

import dash
import dash_bootstrap_components as dbc
from dash import Dash

app = Dash(__name__,
           use_pages=True,
           pages_folder="pages",
           external_stylesheets=[dbc.themes.BOOTSTRAP,
                                 dbc.icons.BOOTSTRAP],
           suppress_callback_exceptions=True,
           )

app.layout = dbc.Container([
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Tracking", href="/")),
            dbc.NavItem(dbc.NavLink("Review", href="/review")),
            dbc.NavItem(dbc.NavLink("Criteria", href="/criteria")),
            dbc.NavItem(dbc.NavLink("Profile", href="/profile")),
        ],
        brand="job-board",
        color="dark",
        dark=True,
        className="mb-4"
    ),
    dash.page_container
], fluid=True)