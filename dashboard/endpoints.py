"""Endpoints."""


from flask import Blueprint, make_response, Response
from src.agents import match_job_from_description, suggest_fill
from datetime import datetime, timedelta
import os
from src.setup import DATA_DIR, config, save_config
from src.utils import load_existing_profile
from flask import request
import pandas as pd
import logging
from src.memory import memory_store
from src.models import AddEntryModel, APIResponseModel

logger = logging.getLogger(__name__)

blueprint = Blueprint("api", __name__)


def api_response(response: APIResponseModel) -> Response:
    return make_response({
        "status": response.status,
        "message": response.message,
        "payload": response.payload},
        response.code)


@blueprint.route("/api/last-sync", methods=["GET"])
def last_sync() -> Response:
    response = APIResponseModel()
    try:
        response.payload["last_sync"] = (
            config.last_sync or (datetime.now() - timedelta(days=2))
            ).isoformat()
    except Exception as e:
        logger.error(e)
        response.code = 400
        response.status = "error"
        response.message = str(e) or type(e).__name__

    return api_response(response)


@blueprint.route("/api/sync-jobs", methods=["POST"])
def sync_jobs() -> Response:
    response = APIResponseModel()
    try:
        data_filepath = os.path.join(DATA_DIR, "jobs.csv")
        jobs = request.json
        logger.info("Job sync requested.")
        new_df = pd.DataFrame(jobs)
        new_df["status"] = "applied"
        new_df["created_at"] = pd.to_datetime(
            new_df["created_at"]).dt.tz_localize(None)
        new_df["applied_at"] = pd.to_datetime(
            new_df["applied_at"]).dt.strftime("%Y-%m-%d %H:%M:%S.%f")
        new_df["posted_time"] = pd.to_datetime(
            new_df["posted_time"]).dt.strftime("%Y-%m-%d %H:%M:%S.%f")

        existing_ids = set()
        if os.path.exists(data_filepath):
            existing_df = pd.read_csv(data_filepath)
            existing_ids = set(existing_df["job_id"].astype(str).values)

        filtered = new_df[~new_df["job_id"].isin(existing_ids)]

        if os.path.exists(data_filepath):
            filtered = filtered.reindex(columns=existing_df.columns)

        added = len(filtered)
        if added:
            filtered.to_csv(
                data_filepath,
                mode="a",
                header=not os.path.exists(data_filepath),
                index=False
            )

        config.last_sync = str(datetime.now())
        save_config(config)
        response.payload = {"added": added, "skipped": len(jobs) - added}
    except Exception as e:
        logger.error(e)
        response.code = 400
        response.status = "error"
        response.message = str(e) or type(e).__name__

    return api_response(response)


@blueprint.route("/api/match-job", methods=["POST"])
def get_match() -> Response:
    response = APIResponseModel()
    try:
        job_description = request.json

        if not job_description:
            response.code = 400
            response.status = "error"
            response.message = "Empty job description"
            return api_response(response)

        profile = load_existing_profile()
        if (
            profile is None or
            not any(
                profile.model_dump(exclude={"years_of_experience"}).values())):
            response.code = 404
            response.status = "error"
            response.message = "No profile found to match"
            return api_response(response)

        result, summary = match_job_from_description(
            job_description=job_description,
            user_profile=profile)

        response.payload = {
            "job_summary": summary.job_summary,
            "relevance_score": result.relevance_score,
            "matching_skills": result.matching_skills,
            "missing_requirements": result.missing_requirements
        }
    except Exception as e:
        logger.error(e)
        response.code = 400
        response.status = "error"
        response.message = str(e) or type(e).__name__

    return api_response(response)


@blueprint.route("/api/remember", methods=["POST"])
def save_to_vector_db() -> Response:
    response = APIResponseModel()
    try:
        entry = AddEntryModel(**request.json)
        memory_entry = memory_store.add_entry(entry)
        if memory_entry:
            response.payload = memory_entry.model_dump()
        else:
            response.message = "Duplicate entry skipped"
    except Exception as e:
        logger.error(e)
        response.code = 400
        response.status = "error"
        response.message = str(e) or type(e).__name__
    return api_response(response)


@blueprint.route("/api/suggest-fill", methods=["POST"])
def suggest_fill_from_vector_db() -> Response:
    response = APIResponseModel()
    try:
        query = request.json
        response.payload = suggest_fill(query).model_dump()
    except Exception as e:
        logger.error(e)
        response.code = 400
        response.status = "error"
        response.message = str(e) or type(e).__name__

    return api_response(response)
