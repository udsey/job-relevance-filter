"""Dash App."""

import dash
import dash_bootstrap_components as dbc
from dash import Dash, Input, Output

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
            dbc.NavItem(dbc.NavLink("Criteria & Profile",
                                    href="/criteria_profile")),
        ],
        brand="job-board",
        color="dark",
        dark=True,
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
