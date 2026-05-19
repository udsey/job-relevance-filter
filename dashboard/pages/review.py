"""Review"""
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dash_table, html


dash.register_page(__name__, path="/review")

def layout():
    return html.Div([])