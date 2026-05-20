"""Review"""
import dash
from dash import html


dash.register_page(__name__, path="/review")


def layout():
    return html.Div([])
