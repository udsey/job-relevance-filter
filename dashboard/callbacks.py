"""Clientside Callbacks."""
from dash import Input, Output


def init_callbacks(app) -> None:
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
