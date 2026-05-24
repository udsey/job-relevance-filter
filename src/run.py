"""Run."""

from datetime import datetime
import logging
import os

import pandas as pd
from src.models import LLMUserProfileModel, SearchCriteria
from src.parser import match_jobs
from src.scraper import find_new_jobs
from src.setup import CONFIG_DIR, DATA_DIR, config, save_config
from src.utils import check_paths, load_yaml

logger = logging.getLogger(__name__)


def run() -> None:
    """Run job find and match."""
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
        processed_ids = set(jobs_df.job_id.astype(str).values.tolist())
        file_exists = True

    fail_runs = 0

    for params in criteria:
        logger.info(f"Searching for jobs that matches: {params}")
        try:
            new_jobs, ids = find_new_jobs(params)
            logging.info(f"Found {len(ids)} new jobs.")

            if not new_jobs:
                continue
            jobs_filtered = [job for job in new_jobs
                             if job.job_id not in processed_ids]

            new_jobs_df = match_jobs(profile, jobs_filtered)
            logging.info(f"Filtered down to {new_jobs_df.shape[0]}")

            if new_jobs_df.empty:
                continue
            processed_ids |= ids
            new_jobs_df.to_csv(
                data_filepath,
                mode='a',
                header=not file_exists,
                index=False)
            file_exists = True
            logging.info(f"{new_jobs_df.shape[0]}"
                         f" new jobs added to {data_filepath}")
        except Exception as e:
            logger.error(f"Error processing criteria {params}: {e}")
            fail_runs += 1
            continue

        if fail_runs != len(criteria):
            config.last_run = datetime.now()
            save_config(config)
