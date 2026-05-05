import logging
import os
import time

from bs4 import BeautifulSoup
import pandas as pd
import requests
from tqdm import tqdm

from scr.models import LinkedInJobsConfig, LinkedinJobModel
from scr.setup import DATA_DIR, config

logger = logging.getLogger(__name__)


def get_job_search_content(config: LinkedInJobsConfig, offset: int) -> str:
    """Creates and sends a request to the LinkedIn Jobs API based on the provided config."""
    params = {}
    
    if config.keywords:
        params['keywords'] = config.keywords.replace(' ', '+')
    
    if config.location:
        params['location'] = config.location.replace(' ', '+')
    
    if config.start:
        params['start'] = offset
    
    if config.time_posted_interval:
        params['f_TPR'] = config.time_posted_interval
    
    if config.experience_level:
        params['f_E'] = config.experience_level
    
    if config.job_type:
        params['f_JT'] = config.job_type
    
    if config.work_type:
        params['f_WT'] = config.work_type
    
    response = requests.get(config.url_search, params=params)

    if response.status_code == 200:
        return response.content
    else:
        logger.error(response.text)
        return ""


def get_job_getails_content(config: LinkedInJobsConfig, id: str) -> str:
    """Get job getails."""
    url = config.url_job + id
    response = requests.get(url)

    if response.status_code == 200:
        return response.content
    
    else:
        logger.error(response.text)
        return ""


def get_job_listing(config: LinkedInJobsConfig, offset: int) -> list:
    
    response = get_job_search_content(config, offset)
    soup = BeautifulSoup(response, "html.parser")

    jobs = []

    for job_data in soup.find_all("li"):
        job = LinkedinJobModel()

        div = soup.find('div')
        job.job_id = div["data-entity-urn"].split(":")[-1]

        job.job_url = job_data.find("a", class_="base-card__full-link")["href"]
        job.job_title = job_data.find("h3", class_="base-search-card__title").get_text(strip=True)

        job.company = job_data.find("h4", class_="base-search-card__subtitle").get_text(strip=True)
        job.location = job_data.find("span", class_="job-search-card__location").get_text(strip=True)



        job.posted_time = job_data.find("time", class_="job-search-card__listdate--new")["datetime"]

        benefit_text = job_data.find("span", class_="job-posting-benefits__text")
        job.benefit = benefit_text.get_text(strip=True) if benefit_text else None
        jobs.append(job)
    logger.info(f"Found {len(jobs)} jobs!")
    return jobs


def collect_all_jobs(config) -> list:
    """Paginate through all available jobs up to max_results"""
    all_jobs = []
    page = 0
    page_size = 25
    
    while len(all_jobs) < config.max_results:
        offset = page * page_size
        jobs_this_page = get_job_listing(config, offset)
        
        if not jobs_this_page:
            break
        
        # Calculate how many more we need
        remaining = config.max_results - len(all_jobs)
        jobs_to_add = jobs_this_page[:remaining]
        all_jobs.extend(jobs_to_add)
        
        # Stop if this was the last page
        if len(jobs_this_page) < page_size:
            break
        
        page += 1
    
    return all_jobs


def add_job_details(config: LinkedInJobsConfig, jobs: LinkedinJobModel) -> list:
    job_list = []
    for job in tqdm(jobs, 
                    total=len(jobs), 
                    desc="Adding job details"):
        
        job_details = get_job_getails_content(config, job.job_id)
        if not job_details:
            continue
        soup = BeautifulSoup(job_details, "html.parser")
        apply_tracking = soup.find("button", {"data-tracking-control-name": "public_jobs_contextual-sign-in-modal_ssr-ui-lib-outlet-button"})
        job.easy_apply = "offsite" not in apply_tracking.find("icon")['data-svg-class-name']

        applicant_info = soup.find("figcaption", class_="num-applicants__caption")
        if applicant_info:
            job.applicants_info = applicant_info.get_text(strip=True)

        description_div = soup.find("div", class_="description__text--rich") 
        job.description = description_div.get_text(strip=True) if description_div else None

        seniority = soup.find("span", class_="description__job-criteria-text--criteria")
        if seniority:
            job.seniority = seniority.get_text(strip=True)

        job.employment_type = soup.find_all("span", class_="description__job-criteria-text--criteria")[1].get_text(strip=True)

        job.job_function = soup.find_all("span", class_="description__job-criteria-text--criteria")[2].get_text(strip=True)

        job.industries = soup.find_all("span", class_="description__job-criteria-text--criteria")[3].get_text(strip=True)

        job_list.append(job.model_dump())
        time.sleep(2)
    return job_list





def find_new_jobs() -> None:
    jobs = collect_all_jobs(config=config)
    jobs = add_job_details(config=config, jobs=jobs)

    jobs = pd.DataFrame(jobs)
    
    filename = os.path.join(DATA_DIR, "jobs.csv")
    n_new = jobs.shape[0]
    

    if os.path.exists(filename):
        existing_df = pd.read_csv(filename)
        combined_df = pd.concat([existing_df, jobs], ignore_index=True)
        combined_df = combined_df.drop_duplicates(subset=['job_id'], keep='last')
        combined_df.to_csv(filename, index=False)
        n_new = existing_df.shape[0] - jobs.shape[0]
    else:
        jobs.to_csv(filename, index=False)

    
    logger.info(f"Done! Saved {n_new} new jobs into {filename}")