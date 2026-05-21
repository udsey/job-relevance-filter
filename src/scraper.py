import logging
import time

from bs4 import BeautifulSoup
import requests

from src.models import LinkedinJobModel, ParamsConfig
from src.setup import config

logger = logging.getLogger(__name__)

LISTING_URL = (
    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search")
DETAILS_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/"


def get_job_search_content(user_params: ParamsConfig, offset: int) -> str:
    """Creates and sends a request to the LinkedIn Jobs API."""

    params = {k: v for k, v in {
        'keywords': user_params.keywords,
        'geoId': user_params.geo_id,
        'f_TPR': user_params.time_posted_interval,
        'f_E': user_params.experience_level,
        'f_JT': user_params.job_type,
        'f_WT': user_params.work_type,
        'start': offset
    }.items() if v is not None}

    response = requests.get(LISTING_URL, params=params)

    if response.status_code == 200:
        return response.content
    else:
        logger.error(response.text)


def get_job_getails_content(id: str) -> str:
    """Get job getails."""
    url = DETAILS_URL + id
    response = requests.get(url)

    if response.status_code == 200:
        return response.content
    else:
        logger.error(response.text)


def get_job_listing(response: str) -> list:
    jobs = []
    soup = BeautifulSoup(response, "html.parser")

    for job_data in soup.find_all("li"):
        if not job_data:
            continue
        try:
            job = LinkedinJobModel()
            div = job_data.find('div')
            job.job_id = div["data-entity-urn"].split(":")[-1]
            url_card = job_data.find("a", class_="base-card__full-link")
            job.job_url = url_card.get("href") if url_card else None
            job.job_title = job_data.find(
                "h3",
                class_="base-search-card__title").get_text(strip=True)
            job.company = job_data.find(
                "h4",
                class_="base-search-card__subtitle").get_text(strip=True)
            job.location = job_data.find(
                "span",
                class_="job-search-card__location").get_text(strip=True)
            posted = job_data.find(
                "time",
                class_="job-search-card__listdate--new")
            job.posted_time = posted.get("datetime") if posted else None
            benefit_text = job_data.find(
                "span",
                class_="job-posting-benefits__text")
            job.benefit = (
                benefit_text.get_text(strip=True) if benefit_text else None)
            jobs.append(job)
        except Exception as e:
            logger.error(e)
            continue
    return jobs


def collect_jobs_with_params(params: ParamsConfig) -> list[LinkedinJobModel]:
    all_jobs = []
    page = 0
    page_size = 25

    while len(all_jobs) < config.max_results:
        offset = page * page_size
        response = get_job_search_content(params, offset=offset)
        if not response:
            break

        jobs = get_job_listing(response)
        if not jobs:
            break

        remaining = config.max_results - len(all_jobs)
        jobs_to_add = jobs[:remaining]
        all_jobs.extend(jobs_to_add)

        if len(jobs) < page_size:
            break
        page += 1
    return all_jobs


def add_job_details(jobs: LinkedinJobModel) -> tuple:
    job_list = []
    ids = set()
    for job in jobs:
        try:
            job_details = get_job_getails_content(job.job_id)
            if not job_details:
                continue
            soup = BeautifulSoup(job_details, "html.parser")
            if not soup:
                continue
            btn = ("public_jobs_contextual-sign-"
                   "in-modal_ssr-ui-lib-outlet-button")
            apply_tracking = soup.find(
                "button", {"data-tracking-control-name": btn})
            apply_icon = apply_tracking.find("icon")
            apply_icon = (apply_icon.get('data-svg-class-name') if apply_icon
                          else "")
            job.easy_apply = "offsite" in apply_icon
            applicant_info = soup.find("figcaption",
                                       class_="num-applicants__caption")
            if applicant_info:
                job.applicants_info = applicant_info.get_text(strip=True)

            description_div = soup.find("div",
                                        class_="description__text--rich")
            job.description = (
                description_div.get_text(strip=False) if description_div
                else None)

            seniority = soup.find(
                "span",
                class_="description__job-criteria-text--criteria")
            if seniority:
                job.seniority = seniority.get_text(strip=True)

            job.employment_type = soup.find_all(
                "span",
                class_="description__job-criteria-text--criteria"
                )[1].get_text(strip=True)

            job.job_function = soup.find_all(
                "span",
                class_="description__job-criteria-text--criteria"
                )[2].get_text(strip=True)

            job.industries = soup.find_all(
                "span",
                class_="description__job-criteria-text--criteria"
                )[3].get_text(strip=True)

            job_list.append(job)

            ids.add(job.job_id)
        except Exception as e:
            logger.error(e)
        finally:
            time.sleep(2)
    return job_list, ids


def find_new_jobs(params) -> tuple:
    jobs = collect_jobs_with_params(params)
    if not jobs:
        return [], set()
    jobs, ids = add_job_details(jobs)
    return jobs, ids
