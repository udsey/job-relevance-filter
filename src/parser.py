import base64
from datetime import datetime
import io
import os

import pandas as pd
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel

import logging

import pdfplumber
from tqdm import tqdm
from src.models import (LLMJobMatchModel, LLMJobSummaryModel,
                        LLMUserProfileModel, LinkedinJobModel)
from src.setup import CONFIG_DIR, config
from dotenv import load_dotenv

from src.utils import save_to_yaml

load_dotenv()

logger = logging.getLogger(__name__)


def get_llm() -> BaseChatModel:
    """Get llm with params."""
    model_type = config.llm_config.model_type

    logger.info(f"Loading {model_type} LLM: {config.llm_config.model_name}")

    if model_type == "groq":
        return ChatGroq(
            model=config.llm_config.model_name,
            temperature=config.llm_config.temperature
        )

    elif model_type == "local":
        return ChatOllama(
            model=config.llm_config.model_name,
            temperature=config.llm_config.temperature
        )

    elif model_type == "deepseek":
        return ChatDeepSeek(
            model=config.llm_config.model_name,
            temperature=config.llm_config.temperature,
            extra_body={"thinking": {"type": "disabled"}}
        )

    else:
        logger.error(
            f"Unknown model type: '{model_type}'. Expected 'groq' or 'local'.")
        raise


llm = get_llm()

match_job_prompt = ChatPromptTemplate.from_messages([
    ("system", config.llm_config.match_job_prompt),
    ("human", "{job}"),
    ("human", "{user_profile}")
    ])

job_summary_prompt = ChatPromptTemplate.from_messages([
    ("system", config.llm_config.job_summary_prompt),
    ("human", "{job}")
    ])

extract_user_profile_prompt = ChatPromptTemplate.from_messages([
    ("system", config.llm_config.extract_user_profile_prompt),
    ("human", "{content}")
    ])

job_matcher_agent = (
    match_job_prompt | llm.with_structured_output(LLMJobMatchModel))

user_profile_extraction_agent = (
    extract_user_profile_prompt |
    llm.with_structured_output(LLMUserProfileModel))

job_summary_extraction_agent = (
    job_summary_prompt |
    llm.with_structured_output(LLMJobSummaryModel))


def match_job(job: LinkedinJobModel,
              user_profile: LLMUserProfileModel) -> LLMJobMatchModel:
    return job_matcher_agent.invoke({
        "job": job.model_dump(),
        "user_profile": user_profile.model_dump()
    })


def get_job_summary(job: LinkedinJobModel) -> LLMJobSummaryModel:
    return job_summary_extraction_agent.invoke({
        "job": job.model_dump()
    })


def extract_user_profile(content: str) -> LLMUserProfileModel:
    return user_profile_extraction_agent.invoke({"content": content})


def match_jobs(profile: LLMUserProfileModel,
               jobs: list[LinkedinJobModel]) -> pd.DataFrame:
    results = []
    for job in tqdm(jobs, desc="Matching jobs", total=len(jobs)):
        try:
            summary = get_job_summary(job=job)
            job.job_summary = summary.job_summary
            match = match_job(user_profile=profile, job=job)
            job_dict = (
                job.model_dump() |
                match.model_dump() |
                {"status": "new",
                 "created_at": datetime.now()})
            results.append(job_dict)
        except Exception as e:
            logger.error(e)

    return pd.DataFrame(results)


def create_user_profile(
        content: str = None,
        filepath: str = None) -> LLMUserProfileModel:
    if not content and not filepath:
        logger.error("Provide content or filepath")
    elif content:
        _, content_string = content.split(",")
        decoded = base64.b64decode(content_string)
        with pdfplumber.open(io.BytesIO(decoded)) as pdf:
            data = "\n".join(page.extract_text() for page in pdf.pages)
    else:
        if not os.path.exists(filepath):
            logger.error(
                "File was not found at {filepath}. Please provide valid path")
            return
        with pdfplumber.open(filepath) as pdf:
            data = '\n'.join(page.extract_text() or '' for page in pdf.pages)

    user_profile = extract_user_profile(data)
    filepath = os.path.join(CONFIG_DIR, "profile.yaml")
    save_to_yaml(user_profile, filepath)
    return user_profile
