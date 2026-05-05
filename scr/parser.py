import pdfplumber
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable

from pydantic import BaseModel
import logging
from scr.models import LLMJobMatchModel, LLMUserProfileModel, LinkedinJobModel
from scr.setup import config

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
    
    else:
        logger.error(f"Unknown model type: '{model_type}'. Expected 'groq' or 'local'.")
        raise


def get_structured_llm(prompt_text: str, output_model: BaseModel) -> Runnable:
    """Return structured llm."""
    


    structured_llm = prompt | llm.with_structured_output(output_model)

    return structured_llm

llm = get_llm()

match_job_prompt = ChatPromptTemplate.from_messages([
    ("system", config.llm_config.match_job_prompt),
    ("human", "{job}"),
    ("human", "{user_profile}")
    ])

extract_user_profile_prompt = ChatPromptTemplate.from_messages([
    ("system", config.llm_config.extract_user_profile_prompt),
    ("human", "{content}")
    ])


job_matcher_agent = match_job_prompt | llm.with_structured_output(LLMJobMatchModel)

user_profile_extraction_agent = extract_user_profile_prompt | llm.with_structured_output(LLMUserProfileModel)


def match_job(job: LinkedinJobModel, 
              user_profile: LLMUserProfileModel) -> LLMJobMatchModel:
    return job_matcher_agent.invoke({
        "job": job.model_dump(),
        "user_profile": user_profile.model_dump()
    })


def extract_user_profile(pdf_path: str) -> LLMUserProfileModel:
    with pdfplumber.open(pdf_path) as pdf:
        text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
    return user_profile_extraction_agent.invoke({"content": text})
    




