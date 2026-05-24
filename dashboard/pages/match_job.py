import os

import dash
from dash import Input, Output, State, callback, html, no_update
from dash import dcc
import dash_bootstrap_components as dbc

from src.parser import match_job_from_description
from src.setup import CONFIG_DIR
from src.utils import load_existing_profile


dash.register_page(__name__, path="/match-job")


def layout() -> html.Div:
    profile = None
    if not os.path.exists(os.path.join(CONFIG_DIR, "profile.yaml")):
        return get_empty_page()
    else:
        profile = load_existing_profile()
        if (profile is None or not any(
                profile.model_dump(exclude={"years_of_experience"}).values())):
            return get_empty_page()
    return html.Div([
        get_input_form(),
        html.Div(id="match-result", hidden=True),
    ])


def get_empty_page() -> html.Div:

    text = html.Div([
            html.P([
                "Go to the ",
                dcc.Link("Profile page", href="/profile"),
                " to generate your profile from CV.",
            ]),
        ])
    return html.Div([
        dbc.Card([
            html.H3("Please create profile first."),
            dbc.CardBody(text),
            dbc.CardImg(src="/static/images/empty_match.jpg", bottom=True),
        ])
    ])


def get_input_form() -> html.Div:
    return html.Div([

        dbc.Textarea(id="job-match-job-description",
                     placeholder="Paste job description"),
        dbc.Button("Match", id="match-job-btn"),
    ])


def match_form(job_summary: str,
               relevance_score: float,
               matching_skills: list[str],
               missing_requirements: list[str]) -> dbc.Card:
    score_color = (
        "info" if relevance_score and relevance_score >= 0.7 else "warning")
    return dbc.Card([
        dbc.CardHeader(
            dbc.Badge(f"Match score: {int(relevance_score * 100)}/100",
                      color=score_color, className="float-end"),
        ),
        dbc.CardBody([
            html.P(job_summary or "", className="small mb-2"),
            dbc.Row([
                    html.Big("Matching:"),
                    html.Div([dbc.Badge(
                        s, color="info", style={"fontWeight": "600"},
                        className="me-1 mt-1") for s in matching_skills]),]),
            dbc.Row([
                    html.Big("Missing:"),
                    html.Div([dbc.Badge(
                        s, color="info", style={"fontWeight": "600"},
                        className="me-1 mt-1") for s in missing_requirements]),
                    ]),
        ])
    ])


@callback(
    Output("match-job-btn", "children", allow_duplicate=True),
    Output("match-job-btn", "disabled", allow_duplicate=True),
    Input("match-job-btn", "n_clicks"),
    State("job-match-job-description", "value"),
    prevent_initial_call=True
)
def on_match_click(n_click, job_description: str):

    if not n_click or not job_description:
        return no_update, no_update
    return [dbc.Spinner(size="sm"), " Matching..."], True


@callback(
    Output("match-job-btn", "children", allow_duplicate=True),
    Output("match-job-btn", "disabled", allow_duplicate=True),
    Input("match-result", "hidden"),
    prevent_initial_call=True
)
def on_match_result(hidden: bool):
    if hidden:
        return no_update, no_update
    return "Match", False


@callback(
    Output("match-result", "children"),
    Output("match-result", "hidden"),
    Input("match-job-btn", "n_clicks"),
    State("job-match-job-description", "value"),
)
def on_match(n_click, job_description: str):

    if not n_click or not job_description:
        return no_update, no_update
    profile = load_existing_profile()
    result, summary = match_job_from_description(
        job_description=job_description,
        user_profile=profile)
    return (
        match_form(
            job_summary=summary.job_summary,
            relevance_score=result.relevance_score,
            matching_skills=result.matching_skills,
            missing_requirements=result.missing_requirements,
        ),
        False,
    )
