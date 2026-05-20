"""Run."""

import os

import pandas as pd
from tqdm import tqdm

from src.models import LLMUserProfileModel, SearchCriteria
from src.parser import match_jobs
from src.scraper import find_new_jobs
from src.setup import CONFIG_DIR, DATA_DIR
from src.utils import check_paths, load_yaml


def find_relevant_jobs() -> None:
    criteria_filepath = os.path.join(CONFIG_DIR, "criteria.yaml")
    profile_filepath = os.path.join(CONFIG_DIR, 'profile.yaml')

    check_paths([criteria_filepath, profile_filepath])

    criteria = load_yaml(criteria_filepath, SearchCriteria)
    profile = load_yaml(profile_filepath, LLMUserProfileModel)

    jobs = None
    file_exists = False
    processed_ids = set()
    filepath = os.path.join(DATA_DIR, "jobs.csv")
    if os.path.exists(filepath):
        jobs = pd.read_csv(filepath)
        processed_ids = set(jobs.job_id.values.tolist())
        file_exists = True

    for params in tqdm(criteria,
                       desc="Finding relevant jobs.",
                       total=len(criteria)):
        job_df = find_new_jobs(params)
        if not job_df or job_df.empty:
            continue
        job_df = job_df = job_df.loc[~job_df['job_id'].isin(processed_ids)]
        filtered_jobs = match_jobs(profile, job_df)
        processed_ids |= job_df.job_id
        filtered_jobs.to_csv(filepath,
                             mode='a',
                             header=not file_exists,
                             index=False)
        file_exists = True
