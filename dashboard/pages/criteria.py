"""Criteria"""
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html, no_update
import json
from scr.utils import create_params_config
from scr.setup import config, save_config

dash.register_page(__name__, path="/criteria")

def layout():
    return html.Div([
        get_criteria_form(),
        html.Button(
            "Save",
            id="save-btn",
            className="nav-btn-save"
        )
    ])


def get_criteria_form():
    return dbc.Card([
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
                        value="r86400"),
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
                        ]),
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
                        ]),
                ], md=3),
                dbc.Col([
                    html.Label("Work type"),
                    dbc.Checklist(
                        id="work-type-select",
                        options=[
                            {"label": "Remote", "value": 1},
                            {"label": "On-site", "value": 2},
                            {"label": "Hybrid", "value": 3},
                        ]),
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
                    html.Div(id="position-tags", className="mt-2"),
                ], md=6),
                dbc.Col([
                    html.Label("Location", className='mb-2'),
                    dbc.Input(
                        id="location-input",
                        placeholder="Add location",
                        type="text"
                    ),
                    html.Div(id="location-tags", className="mt-2"),
                ], md=6),
            ], style={"marginTop": "10px"}),
        ]),
    ])


def add_tag(new_tag_value, existing_tags, tag_id_prefix="tag"):
    """
    Universal function to add a tag to a tag list

    Args:
        new_tag_value: The value/text of the new tag to add
        existing_tags: The existing tag components from html.Div children
        tag_id_prefix: Prefix for the tag ID (default: "tag")

    Returns:
        tuple: (new_tags_list, empty_string_for_input) or (no_update, no_update)
    """
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


def remove_tag(clicked, existing_tags, tag_id_prefix="tag"):
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
    except:
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


def _extract_tag_value(tag_component):
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
                tag_value = children[0] if isinstance(children[0], str) else children[0].get('props', {}).get('children', '')
            elif isinstance(children, str):
                tag_value = children
            else:
                tag_value = str(children)
        elif hasattr(tag_component, 'props'):
            # Component object format
            tag_value = tag_component.props.children[0] if isinstance(tag_component.props.children, list) else tag_component.props.children
            if isinstance(tag_value, list):
                tag_value = tag_value[0]
        else:
            return None

        return tag_value if isinstance(tag_value, str) else None
    except:
        return None


def _create_tag_components(tag_values, tag_id_prefix="tag"):
    """
    Create badge components for tags

    Args:
        tag_values: List of tag values
        tag_id_prefix: Prefix for the tag ID

    Returns:
        list: List of dbc.Badge components
    """
    import dash_bootstrap_components as dbc
    from dash import html

    tags = []
    for tag_value in tag_values:
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
                        id={"type": f"{tag_id_prefix}-remove", "index": tag_value}
                    )
                ],
                color="primary",
                className="me-1 mb-1",
                style={"padding": "8px 12px"}
            )
        )

    return tags


@callback(
    Output("position-tags", "children"),
    Output("position-input", "value"),
    Input("position-input", "n_submit"),
    State("position-input", "value"),
    State("position-tags", "children"),
    prevent_initial_call=True
)
def add_position_callback(n_submit, position_value, existing_tags):
    return add_tag(position_value, existing_tags, tag_id_prefix="position")


@callback(
    Output("position-tags", "children", allow_duplicate=True),
    Input({"type": "position-remove", "index": dash.ALL}, "n_clicks"),
    State("position-tags", "children"),
    prevent_initial_call=True
)
def remove_position_callback(clicked, existing_tags):
    return remove_tag(clicked, existing_tags, tag_id_prefix="position")



@callback(
    Output("location-tags", "children"),
    Output("location-input", "value"),
    Input("location-input", "n_submit"),
    State("location-input", "value"),
    State("location-tags", "children"),
    prevent_initial_call=True
)
def add_location_callback(n_submit, location_value, existing_tags):
    return add_tag(location_value, existing_tags, tag_id_prefix="location")


@callback(
    Output("location-tags", "children", allow_duplicate=True),
    Input({"type": "location-remove", "index": dash.ALL}, "n_clicks"),
    State("location-tags", "children"),
    prevent_initial_call=True
)
def remove_location_callback(clicked, existing_tags):
    return remove_tag(clicked, existing_tags, tag_id_prefix="location")


def save_to_config(experience_level,
                   job_type,
                   work_type,
                   locations,
                   positions,
                   time_interval):
    geo_id_values = [
        v for loc in locations
        if (v := resolve_geo_id(loc)) is not None] or [None]
    search_combinations = product(postions,
                                  geo_id_values,
                                  experience_level,
                                  job_type,
                                  work_type)

    search_params = [
        create_params_config(p, time_interval) for p in search_combinations]
    config.search_parameters = search_params
    save_config(config)

from dash import Input, Output, State, callback
import json

@callback(
    Output("save-status", "children", allow_duplicate=True),
    Input("save-btn", "n_clicks"),
    State("experience-select", "value"),
    State("job-type-select", "value"),
    State("work-type-select", "value"),
    State("position-tags", "children"),
    State("time-select", "value"),
    prevent_initial_call=True
)
def save_criteria(n_clicks, experience_level, job_type, work_type, position_tags, time_interval):
    if not n_clicks:
        return ""

    # Extract positions from tags
    positions = []
    if position_tags:
        for tag in position_tags:
            # Extract position text from tag component
            if isinstance(tag, dict) and 'props' in tag:
                children = tag['props'].get('children', [])
                if isinstance(children, list) and len(children) > 0:
                    position = children[0] if isinstance(children[0], str) else children[0].get('props', {}).get('children', '')
                elif isinstance(children, str):
                    position = children
                else:
                    continue
                if position:
                    positions.append(position)
            elif hasattr(tag, 'props'):
                position = tag.props.children[0] if isinstance(tag.props.children, list) else tag.props.children
                if isinstance(position, list):
                    position = position[0]
                if position:
                    positions.append(position)

    # Handle None values (convert to empty lists for product)
    experience_level = experience_level or []
    job_type = job_type or []
    work_type = work_type or []
    locations = []  # You'll need to add locations input if you have it

    save_to_config(
        experience_level=experience_level,
        job_type=job_type,
        work_type=work_type,
        locations=locations,
        postions=positions,
        time_interval=time_interval
    )

    return "✅ Saved successfully!"

