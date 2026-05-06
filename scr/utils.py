import logging
from itertools import product
import os
import pandas as pd
import questionary
import requests
from tqdm import tqdm
from scr.models import LLMUserProfileModel, LinkedinJobModel, ParamsConfig
from scr.parser import extract_user_profile, match_job
from scr.setup import BASE_DIR, DATA_DIR, config, load_yaml, save_config, save_to_yaml


logger = logging.getLogger(__name__)


def collect_list(question: str) -> list:
    vals = []
    while True:
        val = questionary.text(question).ask()
        if not val:
            break
        vals.append(val)
    return vals


def create_params_config(params: tuple, time_posted_interval: str) -> ParamsConfig:
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


def create_search_criteria() -> None:
    keywords = collect_list("Add job title (empty to finish):")
    locations = collect_list("Add location (empty to finish):")
    
    time_posted_interval = questionary.select(
        "How recent should the jobs be?", 
        choices=["last 24h", "week", "month"]
    ).ask()
    
    experience_level = questionary.checkbox(
        "Experience level:", 
        choices=["Internship", "Entry", "Associate", "Mid-Senior", "Director", "Executive"]
    ).ask()
    
    job_type = questionary.checkbox(
        "Job type:", 
        choices=["Full-time", "Part-time", "Contract", "Temporary", "Internship"]
    ).ask()
    
    work_type = questionary.checkbox(
        "Work type:", 
        choices=["Remote", "On-site", "Hybrid"]
    ).ask()

    experience_level = experience_level or [None]
    job_type = job_type or [None]
    work_type = work_type or [None]
    geo_id_values = [v for loc in locations if (v := resolve_geo_id(loc)) is not None] or [None]
    search_combinations = product(keywords, geo_id_values, experience_level, job_type, work_type)

    search_params = [create_params_config(p, time_posted_interval) for p in search_combinations]    
    config.search_parameters = search_params
    save_config(config)
    logger.info("Done! Search parameters updated.")


def create_user_profile() -> None:
    while True:
        pdf_path = input("Please enter path to your CV in .pdf format: ")
        if not os.path.exists(pdf_path):
            logger.info("File was not found. Please provide valid path")
            continue
        break
    user_profile = extract_user_profile(pdf_path)
    filepath = os.path.join(BASE_DIR, "user_profile.yaml")
    save_to_yaml(user_profile, filepath)
    logger.info(f"Done. Profile was saved at {filepath}")


def match_jobs() -> None:
    filepath = os.path.join(BASE_DIR, 'user_profile.yaml')
    if not os.path.exists(filepath):
        logger.info(f"User profile not foud at {filepath}")
        return
    user_profile = LLMUserProfileModel(**load_yaml(filepath))

    filepath = os.path.join(DATA_DIR, 'jobs.csv')
    if not os.path.exists(filepath):
        logger.info(f"File {filepath} not found.")
        return
    jobs = pd.read_csv(filepath, dtype=str, na_filter=False)
    if jobs.empty:
        logger.info("Empty file.")
    
        return
    
    results = []
    for _, job in tqdm(jobs.iterrows(),
                       desc="Matching jobs.",
                       total=jobs.shape[0]):
        job = LinkedinJobModel(**job)
        result = match_job(user_profile=user_profile,
                           job=job)
        results.append(result.model_dump())
        
    results = pd.DataFrame(results)
    results.index = jobs.index
    jobs = pd.concat([jobs, results], axis=1)
    jobs.to_csv(filepath, index=False)
    logger.info(f"Done! File {filepath} updated with matching results.")