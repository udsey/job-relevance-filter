"""Run."""

import os

import pandas as pd
from tqdm import tqdm

from src.models import LLMUserProfileModel, SearchCriteria
from src.parser import match_jobs
from src.scraper import find_new_jobs
from src.setup import CONFIG_DIR, DATA_DIR
from src.utils import check_paths, load_yaml


def run() -> None:
    criteria_filepath = os.path.join(CONFIG_DIR, "criteria.yaml")
    profile_filepath = os.path.join(CONFIG_DIR, 'profile.yaml')

    check_paths([criteria_filepath, profile_filepath])

    criteria = load_yaml(criteria_filepath, SearchCriteria).search_parameters
    profile = load_yaml(profile_filepath, LLMUserProfileModel)

    file_exists = False
    processed_ids = set()
    data_filepath = os.path.join(DATA_DIR, "jobs.csv")
    if os.path.exists(data_filepath):
        jobs_df = pd.read_csv(data_filepath)
        processed_ids = set(jobs_df.job_id.values.tolist())
        file_exists = True

    for params in tqdm(criteria,
                       desc="Finding relevant jobs.",
                       total=len(criteria)):
        new_jobs, ids = find_new_jobs(params)
        if not new_jobs:
            continue
        jobs_filtered = [job for job in new_jobs
                         if job.job_id not in processed_ids]
        new_jobs_df = match_jobs(profile, jobs_filtered)
        if new_jobs_df.empty:
            continue
        processed_ids |= ids
        new_jobs_df.to_csv(data_filepath,
                           mode='a',
                           header=not file_exists,
                           index=False)
        file_exists = True
