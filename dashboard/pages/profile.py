"""Criteria"""
import logging
from typing import Any
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html, no_update, dcc
import json
from src.utils import (save_to_config,
                       load_existing_criteria, load_existing_profile,
                       save_profile)
from src.parser import create_user_profile

dash.register_page(__name__, path="/profile")

has_profile = False


def layout() -> html.Div:
    criteria = load_existing_criteria()
    profile = load_existing_profile()
    has_profile = (
            profile is not None and any(
                profile.model_dump(exclude={"years_of_experience"}).values()))
    return html.Div([
        get_criteria_form(criteria),
        html.Div(get_drop_resume_form(),
                 id="upload-card",
                 hidden=has_profile),
        html.Br(),
        html.Div(get_profile_form(profile),
                 id="profile-form-container",
                 hidden=not has_profile),

        dcc.Store(id="position-store", data=criteria.get('positions', [])),
        dcc.Store(id="location-store", data=criteria.get('locations', [])),
        dcc.Store(id="skill-store", data=profile.technical_skills),
        dcc.Store(id="title-store", data=profile.title_history),
        dcc.Store(id="certificate-store", data=profile.certifications),
        dcc.Store(id="profile-dirty", data=False)
    ])


def get_criteria_form(criteria) -> dbc.Card:
    return dbc.Card([
        dbc.CardHeader("Search Criteria:"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Time posted"),
                    dbc.RadioItems(
                        id='time-select',
                        options=[
                            {"label": "last 24 h", "value": "r86400"},
                            {"label": "last week", "value": "r604800"},
                            {"label": "last month", "value": "r2592000"},
                        ],
                        value=criteria.get("time_interval", [None])[0]),
                ], md=3),
                dbc.Col([
                    html.Label("Experience level"),
                    dbc.Checklist(
                        id="experience-select",
                        options=[
                            {"label": "Internship", "value": 1},
                            {"label": "Entry", "value": 2},
                            {"label": "Associate", "value": 3},
                            {"label": "Mid-Senior", "value": 4},
                            {"label": "Director", "value": 5},
                            {"label": "Executive", "value": 6},
                        ],
                        value=criteria.get('experience_level', [])),
                ], md=3),
                dbc.Col([
                    html.Label("Job type"),
                    dbc.Checklist(
                        id="job-type-select",
                        options=[
                            {"label": "Full-time", "value": "F"},
                            {"label": "Part-time", "value": "P"},
                            {"label": "Contract", "value": "C"},
                            {"label": "Temporary", "value": "T"},
                            {"label": "Internship", "value": "I"},
                        ],
                        value=criteria.get('job_type', [])),
                ], md=3),
                dbc.Col([
                    html.Label("Work type"),
                    dbc.Checklist(
                        id="work-type-select",
                        options=[
                            {"label": "Remote", "value": 1},
                            {"label": "On-site", "value": 2},
                            {"label": "Hybrid", "value": 3},
                        ],
                        value=criteria.get('work_type', [])),
                ], md=3),
            ]),
            dbc.Row([
                dbc.Col([
                    html.Label("Job Title", className='mb-2'),
                    dbc.Input(
                        id="position-input",
                        placeholder="Add job title",
                        type="text"
                    ),
                    html.Div(
                        _create_tag_components(criteria.get('positions', []),
                                               "position"),
                        id="position-tags", className="mt-2"
                        ),
                ], md=6),
                dbc.Col([
                    html.Label("Location", className='mb-2'),
                    dbc.Input(
                        id="location-input",
                        placeholder="Add location",
                        type="text"
                    ),
                    html.Div(
                        _create_tag_components(criteria.get('locations', []),
                                               "location"),
                        id="location-tags", className="mt-2"
                        ),
                ], md=6),
            ], style={"marginTop": "10px"}),
        ]),
        dbc.CardFooter([
            html.Button(
                "Save",
                id="save-criteria-btn",
                className="nav-btn-save"),
        ])
    ])


def get_drop_resume_form() -> dbc.Card:
    return dbc.Card([
        dbc.CardHeader("Profile"),
        dbc.CardBody([
            dcc.Upload(
                id="resume-upload",
                className="upload-drop",
                children=html.Div(
                    ["Drop your resume here or ",
                     html.A("select file")]),
                style={"display": "none" if has_profile else "block"}
            ),
            dcc.Loading(
                html.Button(
                    "Generate Profile",
                    id="generate-profile-btn",
                    className="btn",
                    style={
                        "display": "none" if has_profile else "block"}
                ), type="circle"),

        ]),
        ])


def get_profile_form(profile) -> dbc.Card:
    skills = _create_tag_components(profile.technical_skills, "skill")
    titles = _create_tag_components(profile.title_history, "title")
    certifications = _create_tag_components(profile.certifications,
                                            "certificate")
    return dbc.Card([
        dbc.CardHeader([
            "Profile",
            dbc.Button([html.I(className="bi bi-arrow-clockwise")],
                       size="sm", id="re-generate-btn", className="float-end",
                       title="Re-generate profile"),
            ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Current Positon", className='mb-2'),
                    dcc.Input(
                        id="current-position-input",
                        value=profile.current_title,
                        placeholder="Input your current job title"
                    )
                ], md=6),
                dbc.Col([
                    html.Label("Years of relevant experience",
                               className='mb-2'),
                    dcc.Input(
                        id="years-experience-input",
                        value=profile.years_of_experience,
                        placeholder="Input number of years of experience"
                    )
                ], md=6),
            ]),
            dbc.Row([
                dbc.Col([
                    html.Label("Skills", className='mb-2'),
                    dcc.Input(
                        id="skill-input",
                        placeholder="Enter new skill"
                    ),
                    html.Div(skills, id="skill-tags", className="mt-2")

                ]),
            ], style={"marginTop": "10px"}
            ),
            dbc.Row([
                dbc.Col([
                    html.Label("Titles", className='mb-2'),
                    dcc.Input(
                        id="title-input",
                        placeholder="Enter new title"
                    ),
                    html.Div(titles, id="title-tags", className="mt-2")
                ], md=6),
                dbc.Col([
                    html.Label("Certificates", className='mb-2'),
                    dcc.Input(
                        id="certificate-input",
                        placeholder="Enter new certificate"
                    ),
                    html.Div(certifications,
                             id="certificate-tags",
                             className="mt-2")

                ], md=6),
            ], style={"marginTop": "10px"}
            ),
            dbc.Row([
                html.Label("Summary (generated by LLM)"),
                dcc.Textarea(
                    id="summary-input",
                    value=profile.summary,
                    placeholder="Input experience summary",
                    style={"height": "150px"}
                )
            ], style={"marginTop": "10px"}),
        ]),
        dbc.CardFooter([
            html.Button(
                "Save",
                id="save-profile-btn",
                className="nav-btn-save",
            ),
        ]),
            ])


def add_tag(new_tag_value, existing_tags, tag_id_prefix="tag") -> tuple:
    """Universal function to add a tag to a tag list"""
    if not new_tag_value or not new_tag_value.strip():
        return no_update, no_update

    # Get existing tag values
    tag_values = []
    if existing_tags:
        for tag in existing_tags:
            tag_value = _extract_tag_value(tag)
            if tag_value and tag_value not in tag_values:
                tag_values.append(tag_value)

    # Add new tag if not duplicate
    new_tag = new_tag_value.strip()
    if new_tag and new_tag not in tag_values:
        tag_values.append(new_tag)
    else:
        return no_update, no_update

    # Create tags
    tags = _create_tag_components(tag_values, tag_id_prefix)

    return tags, ""


def remove_tag(clicked, existing_tags, tag_id_prefix="tag") -> tuple:
    """
    Universal function to remove a tag from a tag list

    Args:
        clicked: The clicked values from the callback (n_clicks)
        existing_tags: The existing tag components from html.Div children
        tag_id_prefix: Prefix for the tag ID (default: "tag")

    Returns:
        list: New tags list or no_update
    """
    from dash import callback_context

    # Check if any button was clicked
    ctx = callback_context
    if not ctx.triggered or not any(clicked):
        return no_update

    # Get the ID of the clicked button
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        button_id = json.loads(trigger_id)
        tag_to_remove = button_id["index"]
    except Exception as e:
        logging.error(e)
        return no_update

    # Get existing tag values (excluding the one to remove)
    tag_values = []
    if existing_tags:
        for tag in existing_tags:
            tag_value = _extract_tag_value(tag)
            if tag_value and tag_value != tag_to_remove:
                tag_values.append(tag_value)

    # Create new tags without the removed tag
    tags = _create_tag_components(tag_values, tag_id_prefix)

    return tags


def _extract_tag_value(tag_component) -> Any:
    """
    Extract the text value from a tag component

    Args:
        tag_component: A dash component (dict or object) representing a tag

    Returns:
        str: The extracted tag value or None
    """
    try:
        if isinstance(tag_component, dict) and 'props' in tag_component:
            # Dash component dict format
            children = tag_component['props'].get('children', [])
            if isinstance(children, list) and len(children) > 0:
                tag_value = (
                    children[0] if isinstance(children[0], str)
                    else children[0].get('props', {}).get('children', ''))
            elif isinstance(children, str):
                tag_value = children
            else:
                tag_value = str(children)
        elif hasattr(tag_component, 'props'):
            # Component object format
            tag_value = (
                tag_component.props.children[0]
                if isinstance(tag_component.props.children, list)
                else tag_component.props.children)
            if isinstance(tag_value, list):
                tag_value = tag_value[0]
        else:
            return None

        return tag_value if isinstance(tag_value, str) else None
    except Exception as e:
        logging.error(e)
        return None


def _create_tag_components(tag_values, tag_id_prefix="tag") -> Any:
    """
    Create badge components for tags

    Args:
        tag_values: List of tag values
        tag_id_prefix: Prefix for the tag ID

    Returns:
        list: List of dbc.Badge components
    """
    tags = []
    tag_values = [] if tag_values is None else tag_values
    for tag_value in tag_values:
        if tag_value is None:
            continue
        tags.append(
            dbc.Badge(
                [
                    tag_value,
                    html.Span(
                        "✕",
                        style={
                            "cursor": "pointer",
                            "marginLeft": "8px",
                            "fontSize": "12px"
                        },
                        id={"type": f"{tag_id_prefix}-remove",
                            "index": tag_value}
                    )
                ],
                className="tag",
            )
        )

    return tags


@callback(
    Output("position-tags", "children"),
    Output("position-input", "value"),
    Output("position-store", "data"),  # add this
    Input("position-input", "n_submit"),
    State("position-input", "value"),
    State("position-tags", "children"),
    State("position-store", "data"),   # add this
    prevent_initial_call=True
)
def add_position_callback(n_submit, position_value,
                          existing_tags, stored) -> tuple:
    tags, cleared = add_tag(position_value, existing_tags,
                            tag_id_prefix="position")
    if tags is no_update:
        return no_update, no_update, no_update
    new_stored = [t.children[0] for t in tags]
    return tags, cleared, new_stored


@callback(
    Output("position-tags", "children", allow_duplicate=True),
    Output("position-store", "data", allow_duplicate=True),  # add this
    Input({"type": "position-remove", "index": dash.ALL}, "n_clicks"),
    State("position-tags", "children"),
    prevent_initial_call=True
)
def remove_position_callback(clicked, existing_tags) -> tuple:
    tags = remove_tag(clicked, existing_tags, tag_id_prefix="position")
    if tags is no_update:
        return no_update, no_update
    new_stored = [t.children[0] for t in tags]
    return tags, new_stored


@callback(
    Output("location-tags", "children"),
    Output("location-input", "value"),
    Output("location-store", "data"),
    Input("location-input", "n_submit"),
    State("location-input", "value"),
    State("location-tags", "children"),
    State("location-store", "data"),
    prevent_initial_call=True
)
def add_location_callback(n_submit, location_value,
                          existing_tags, stored) -> tuple:
    tags, cleared = add_tag(location_value,
                            existing_tags,
                            tag_id_prefix="location")
    if tags is no_update:
        return no_update, no_update, no_update
    new_stored = [t.children[0] for t in tags]
    return tags, cleared, new_stored


@callback(
    Output("location-tags", "children", allow_duplicate=True),
    Output("location-store", "data", allow_duplicate=True),
    Input({"type": "location-remove", "index": dash.ALL}, "n_clicks"),
    State("location-tags", "children"),
    prevent_initial_call=True
)
def remove_location_callback(clicked, existing_tags) -> tuple:
    tags = remove_tag(clicked, existing_tags, tag_id_prefix="location")
    if tags is no_update:
        return no_update, no_update
    new_stored = [t.children[0] for t in tags]
    return tags, new_stored


@callback(
    Output("skill-tags", "children"),
    Output("skill-input", "value"),
    Output("skill-store", "data"),  # add this
    Input("skill-input", "n_submit"),
    State("skill-input", "value"),
    State("skill-tags", "children"),
    State("skill-store", "data"),   # add this
    prevent_initial_call=True
)
def add_skills_callback(n_submit, skills_value,
                        existing_tags, stored) -> tuple:
    tags, cleared = add_tag(skills_value, existing_tags, tag_id_prefix="skill")
    if tags is no_update:
        return no_update, no_update, no_update
    new_stored = [t.children[0] for t in tags]
    return tags, cleared, new_stored


@callback(
    Output("skill-tags", "children", allow_duplicate=True),
    Output("skill-store", "data", allow_duplicate=True),
    Input({"type": "skill-remove", "index": dash.ALL}, "n_clicks"),
    State("skill-tags", "children"),
    prevent_initial_call=True
)
def remove_skills_callback(clicked, existing_tags) -> tuple:
    tags = remove_tag(clicked, existing_tags, tag_id_prefix="skill")
    if tags is no_update:
        return no_update, no_update
    new_stored = [t.children[0] for t in tags]
    return tags, new_stored


@callback(
    Output("title-tags", "children"),
    Output("title-input", "value"),
    Output("title-store", "data"),  # add this
    Input("title-input", "n_submit"),
    State("title-input", "value"),
    State("title-tags", "children"),
    State("title-store", "data"),   # add this
    prevent_initial_call=True
)
def add_titles_callback(n_submit, titles_value,
                        existing_tags, stored) -> tuple:
    tags, cleared = add_tag(titles_value, existing_tags, tag_id_prefix="title")
    if tags is no_update:
        return no_update, no_update, no_update
    new_stored = [t.children[0] for t in tags]
    return tags, cleared, new_stored


@callback(
    Output("title-tags", "children", allow_duplicate=True),
    Output("title-store", "data", allow_duplicate=True),  # add this
    Input({"type": "title-remove", "index": dash.ALL}, "n_clicks"),
    State("title-tags", "children"),
    prevent_initial_call=True
)
def remove_titles_callback(clicked, existing_tags) -> tuple:
    tags = remove_tag(clicked, existing_tags, tag_id_prefix="title")
    if tags is no_update:
        return no_update, no_update
    new_stored = [t.children[0] for t in tags]
    return tags, new_stored


@callback(
    Output("certificate-tags", "children"),
    Output("certificate-input", "value"),
    Output("certificate-store", "data"),  # add this
    Input("certificate-input", "n_submit"),
    State("certificate-input", "value"),
    State("certificate-tags", "children"),
    State("certificate-store", "data"),   # add this
    prevent_initial_call=True
)
def add_certificates_callback(n_submit, certificates_value,
                              existing_tags, stored) -> tuple:
    tags, cleared = add_tag(certificates_value,
                            existing_tags,
                            tag_id_prefix="certificate")
    if tags is no_update:
        return no_update, no_update, no_update
    new_stored = [t.children[0] for t in tags]
    return tags, cleared, new_stored


@callback(
    Output("certificate-tags", "children", allow_duplicate=True),
    Output("certificate-store", "data", allow_duplicate=True),  # add this
    Input({"type": "certificate-remove", "index": dash.ALL}, "n_clicks"),
    State("certificate-tags", "children"),
    prevent_initial_call=True
)
def remove_certificates_callback(clicked, existing_tags) -> tuple:
    tags = remove_tag(clicked, existing_tags, tag_id_prefix="certificate")
    if tags is no_update:
        return no_update, no_update
    new_stored = [t.children[0] for t in tags]
    return tags, new_stored


@callback(
    Output("save-criteria-btn", "children", allow_duplicate=True),
    Input("save-criteria-btn", "n_clicks"),
    State("experience-select", "value"),
    State("job-type-select", "value"),
    State("work-type-select", "value"),
    State("time-select", "value"),
    State("position-store", "data"),
    State("location-store", "data"),
    prevent_initial_call=True
)
def save_criteria(n_clicks,
                  experience_level,
                  job_type, work_type,
                  time_interval,
                  positions: list[str],
                  locations: list[str]) -> str:
    if not n_clicks:
        return no_update
    try:
        experience_level = experience_level or [None]
        job_type = job_type or [None]
        work_type = work_type or [None]
        save_to_config(
            experience_level=experience_level,
            job_type=job_type,
            work_type=work_type,
            locations=locations,
            positions=positions,
            time_interval=time_interval
        )
        return "Saved"
    except Exception as e:
        logging.error(e)
        return f"Failed: {e}"


@callback(
    Output("save-profile-btn", "children", allow_duplicate=True),
    Output("profile-form-container", "hidden", allow_duplicate=True),
    Output("upload-card", "hidden", allow_duplicate=True),
    Output("resume-upload", "style", allow_duplicate=True),
    Output("generate-profile-btn", "style", allow_duplicate=True),
    Input("save-profile-btn", "n_clicks"),
    State("summary-input", "value"),
    State("skill-store", "data"),
    State("current-position-input", "value"),
    State("title-store", "data"),
    State("certificate-store", "data"),
    State("years-experience-input", "value"),
    prevent_initial_call=True
)
def on_save_profile(n_clicks, summary, technical_skills, current_title,
                    title_history, certifications, years_of_experience):
    if not n_clicks:
        return (no_update, no_update, no_update, no_update, no_update)
    try:
        save_profile(summary, technical_skills, current_title,
                     title_history, certifications, years_of_experience)
        return ("Saved", no_update, no_update, no_update, no_update)
    except Exception as e:
        logging.error(e)
        hidden = {"display": "block"}
        return (f"Failed: {e}", True, False, hidden, hidden)


@callback(
    Output("save-profile-btn", "children"),
    Input("profile-dirty", "data"),
    prevent_initial_call=True
)
def reset_save_profile_btn(dirty) -> Any:
    return "Save" if dirty else no_update


@callback(
    Output("profile-form-container", "children", allow_duplicate=True),
    Output("profile-form-container", "hidden", allow_duplicate=True),
    Output("upload-card", "hidden", allow_duplicate=True),
    Output("resume-upload", "style", allow_duplicate=True),
    Output("generate-profile-btn", "style", allow_duplicate=True),
    Output("skill-store", "data", allow_duplicate=True),
    Output("title-store", "data", allow_duplicate=True),
    Output("certificate-store", "data", allow_duplicate=True),
    Input("generate-profile-btn", "n_clicks"),
    State("resume-upload", "contents"),
    State("resume-upload", "filename"),
    prevent_initial_call=True
)
def generate_profile(n_clicks, contents, filename):
    if not contents:
        return (no_update, no_update, no_update, no_update,
                no_update, no_update, no_update, no_update)
    profile = create_user_profile(contents)

    hidden = {"display": "none"}
    return (
        get_profile_form(profile),
        False,
        True,
        hidden, hidden,
        profile.technical_skills or [],
        profile.title_history or [],
        profile.certifications or [],
    )


@callback(
    Output("profile-form-container", "hidden", allow_duplicate=True),
    Output("upload-card", "hidden", allow_duplicate=True),
    Output("resume-upload", "style", allow_duplicate=True),
    Output("generate-profile-btn", "style", allow_duplicate=True),
    Input("re-generate-btn", "n_clicks"),
    prevent_initial_call=True
)
def on_re_generate(n_clicks) -> tuple:
    """Hide profile form and show drop/resume upload form."""
    if not n_clicks:
        return no_update, no_update, no_update, no_update
    return True, False, {"display": "block"}, {"display": "block"}


@callback(
    Output("profile-dirty", "data"),
    Input("skill-store", "data"),
    Input("title-store", "data"),
    Input("certificate-store", "data"),
    prevent_initial_call=True
)
def mark_dirty(*_) -> bool:
    return True


@callback(
    Output("resume-upload", "children"),
    Input("resume-upload", "filename"),
    prevent_initial_call=True
)
def on_file_uploaded(filename) -> str:
    if filename:
        return html.Div([filename, html.I(className="bi bi-check-lg me-2")])
    return html.Div(["Drop your resume here or ", html.A("select file")])
