from collections import defaultdict
from datetime import date
import logging
from itertools import product
import os
from pydantic import BaseModel
import questionary
import requests
import yaml
from src.models import (LLMUserProfileModel, ParamsConfig,
                        SearchCriteria)
from src.setup import CONFIG_DIR


logger = logging.getLogger(__name__)


def load_yaml(filepath: str, model: BaseModel | None = None):
    if not os.path.exists(filepath):
        data = {}
    else:
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)
    if not model:
        return data
    return model(**data)


def save_to_yaml(data: BaseModel | dict, filepath: str, mode: str = 'w'):
    if isinstance(data, BaseModel):
        data = data.model_dump()
    with open(filepath, mode) as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def collect_list(question: str) -> list:
    vals = []
    while True:
        val = questionary.text(question).ask()
        if not val:
            break
        vals.append(val)
    return vals


def create_params_config(
        params: tuple, time_posted_interval: str) -> ParamsConfig:
    return ParamsConfig(keywords=params[0],
                        geo_id=params[1],
                        experience_level=params[2],
                        job_type=params[3],
                        work_type=params[4],
                        time_posted_interval=time_posted_interval)


def resolve_geo_id(location: str) -> str | None:
    url = "https://www.linkedin.com/jobs-guest/api/typeaheadHits"
    params = {
        "origin": "jserp",
        "typeaheadType": "GEO",
        "geoTypes": "POPULATED_PLACE,ADMIN_DIVISION_TYPE,COUNTRY_REGION",
        "query": location
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        hits = response.json()
        if hits:
            return hits[0].get("id")
    logger.warning(f"Could not resolve geoId for: {location}")
    return None


def _resolve_location(loc: str, locations_dict: dict) -> int | None:
    return locations_dict.get(loc.lower()) or resolve_geo_id(loc)


def save_to_config(experience_level,
                   job_type,
                   work_type,
                   locations,
                   positions,
                   time_interval) -> None:
    filepath = os.path.join(CONFIG_DIR, "locations.yaml")
    locations_dict = load_yaml(filepath)
    geo_id_values = [
        v for loc in locations if (
            v := _resolve_location(loc, locations_dict)) is not None] or [None]
    locations_dict.update({k: v for k, v in zip(geo_id_values, locations)})

    filepath = os.path.join(CONFIG_DIR, "locations.yaml")
    save_to_yaml(locations_dict, filepath)

    search_combinations = product(positions,
                                  geo_id_values,
                                  experience_level,
                                  job_type,
                                  work_type)
    search_params = [
        create_params_config(p, time_interval) for p in search_combinations]
    criteria = SearchCriteria(search_parameters=search_params)
    filepath = os.path.join(CONFIG_DIR, "criteria.yaml")
    save_to_yaml(criteria, filepath)


def load_existing_criteria() -> SearchCriteria | None:
    filepath = os.path.join(CONFIG_DIR, "criteria.yaml")
    criteria = load_yaml(filepath, SearchCriteria)

    filepath = os.path.join(CONFIG_DIR, "locations.yaml")
    location_map = load_yaml(filepath)

    criteria_dict = defaultdict(set)
    for params in criteria.search_parameters:
        criteria_dict["experience_level"].add(params.experience_level)
        criteria_dict["positions"].add(params.keywords)
        criteria_dict["job_type"].add(params.job_type)
        criteria_dict["work_type"].add(params.work_type)
        criteria_dict["time_interval"].add(params.time_posted_interval)
        if params.geo_id:
            criteria_dict["locations"].add(location_map[params.geo_id])
        else:
            criteria_dict["locations"].add(None)

    criteria_dict = {k: list(v) for k, v in criteria_dict.items()}
    return criteria_dict


def load_existing_profile() -> LLMUserProfileModel | None:
    filepath = os.path.join(CONFIG_DIR, "profile.yaml")
    profile = load_yaml(filepath, LLMUserProfileModel)
    return profile


def save_profile(summary, technical_skills, current_title, title_history,
                 certifications, years_of_experience) -> None:
    profile = LLMUserProfileModel(
        summary=summary,
        technical_skills=technical_skills,
        current_title=current_title,
        title_history=title_history,
        certifications=certifications,
        first_experience_year=date.today().year - int(years_of_experience)
    )
    filepath = os.path.join(CONFIG_DIR, "profile.yaml")
    save_to_yaml(profile, filepath)


def check_paths(filepaths: list[str]):
    missing = []
    for filepath in filepaths:
        if not os.path.exists(filepath):
            missing.append(filepath)
    if missing:
        logger.error(f"Missing files: {missing}")
