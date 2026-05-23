from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, computed_field, field_validator


_TIME_MAP = {
    "last 24h": "r86400",
    "week": "r604800",
    "month": "r2592000"}
_EXP_MAP = {
    "Internship": 1,
    "Entry": 2,
    "Associate": 3,
    "Mid-Senior": 4,
    "Director": 5,
    "Executive": 6}
_JOB_MAP = {
    "Full-time": "F",
    "Part-time": "P",
    "Contract": "C",
    "Temporary": "T",
    "Internship": "I"}
_WORK_MAP = {"On-site": 1, "Remote": 2, "Hybrid": 3}


class ParamsConfig(BaseModel):
    """Configuration model for LinkedIn Jobs API request."""
    keywords: Optional[str] = None
    geo_id: Optional[str] = None
    time_posted_interval: Optional[
        Literal["r86400", "r604800", "r2592000"]] = "r86400"
    experience_level: Optional[Literal[1, 2, 3, 4, 5, 6]] = None
    job_type: Optional[Literal["F", "P", "C", "T", "I"]] = None
    work_type: Optional[Literal[1, 2, 3]] = None

    @field_validator("time_posted_interval", mode="before")
    def map_time(cls, v): return _TIME_MAP.get(v, v)

    @field_validator("experience_level", mode="before")
    def map_exp(cls, v): return _EXP_MAP.get(v, v)

    @field_validator("job_type", mode="before")
    def map_job(cls, v): return _JOB_MAP.get(v, v)

    @field_validator("work_type", mode="before")
    def map_work(cls, v): return _WORK_MAP.get(v, v)


class SearchCriteria(BaseModel):
    """User configurations."""
    search_parameters: Optional[List[ParamsConfig]] = []


class LinkedinJobModel(BaseModel):
    """Model for LinekedIn Job."""

    job_id: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    job_url: Optional[str] = None
    posted_time: Optional[str] = None
    posted_time: Optional[str] = None
    posted_text: Optional[str] = None
    benefit: Optional[str] = None

    applicants_info: Optional[str] = None
    description: Optional[str] = None
    seniority: Optional[str] = None
    employment_type: Optional[str] = None
    job_function: Optional[str] = None
    industries: Optional[str] = None

    easy_apply: Optional[bool] = False
    job_summary: Optional[str] = None

    def __str__(self) -> str:
        return "\n".join(f"{k}: {v}" for k, v in self.__dict__.items())


class LLMConfigModel(BaseModel):
    model_type: Optional[Literal["local", "groq", "deepseek"]] = "local"
    temperature: Optional[float] = 0.0
    model_name: Optional[str] = "llama3.2:3b"
    match_job_prompt: Optional[str] = ""
    extract_user_profile_prompt: Optional[str] = ""
    job_summary_prompt: Optional[str] = ""


class Config(BaseModel):
    max_results: Optional[int] = 25
    cron: Optional[str] = "0 9 * * *"
    relevance_threshold: Optional[float] = 0.7
    no_response_days: Optional[int] = 14
    llm_config: Optional[LLMConfigModel] = LLMConfigModel()
    last_run: Optional[date] = None


class LLMJobSummaryModel(BaseModel):
    job_summary: str = Field(
        description="A concise 4-7 sentence human-friendly summary "
        "of the job posting. "
        "Structure as: (1) what the company does and the role's purpose, "
        "(2) key responsibilities in plain language, "
        "(3) must-have requirements and nice-to-haves, "
        "(4) practical details: location, employment type, seniority level, "
        "and any compensation or benefits if mentioned. "
        "Avoid corporate jargon. Write as if explaining the job to a friend. "
        "Example: 'Acme Corp, a fintech startup, is looking for a mid-level "
        "Python developer to help build their fraud detection pipeline. "
        "You'll mostly work on backend APIs and data pipelines "
        "with some ML involvement. "
        "They need 3+ years of Python and SQL; Spark experience is a bonus. "
        "It's a remote full-time role, likely targeting senior "
        "engineers based on the description.'"
        )


class LLMJobMatchModel(BaseModel):
    relevance_score: float = Field(
        description="Float score between 0.0 and 1.0 indicating "
        "how well the user's profile, skills, and experience match the job "
        "position requirements. 1.0 = perfect match/excellent fit, "
        "0.7-0.9 = strong match, 0.4-0.6 = partial match, "
        "0.1-0.3 = weak match, 0.0 = no match/not suitable."
    )

    confidence_level: float = Field(
        description="Numerical confidence score between 0.0 and 1.0 "
        "representing the LLM's certainty in the relevance assessment. "
        "1.0 = extremely confident based on clear evidence, "
        "0.0 = completely uncertain or contradictory information found."
    )

    reason: str = Field(
        description="Detailed explanation for the relevance decision, "
        "structured as a concise paragraph. "
        "Should include: (1) key matching skills/qualifications, "
        "(2) identified gaps or missing requirements, "
        "(3) specific evidence from user info, "
        "(4) any contextual factors that influenced the assessment. "
        "Use clear, actionable language."
    )

    # Optional: Additional helpful fields
    matching_skills: Optional[list[str]] = Field(
        default=None,
        description="List of specific skills, experiences, "
        "or qualifications from the user's profile that "
        "positively match the job requirements. "
        "Extract exact phrases from user info when possible."
    )

    missing_requirements: Optional[list[str]] = Field(
        default=None,
        description="List of critical job requirements not found"
        " in the user's profile. "
        "Focus on deal-breakers and mandatory qualifications."
    )

    recommendation: Optional[str] = Field(
        default=None,
        description="Brief actionable recommendation for next steps. "
        "Examples: 'Proceed to interview', "
        "'Consider for training program', "
        "'Not suitable - lacks X years of experience', or '"
        "Further screening needed for Y skill'."
    )

    def __str__(self) -> str:
        return "\n".join(f"{k}: {v}" for k, v in self.__dict__.items())

    @field_validator('relevance_score', 'confidence_level', mode='before')
    @classmethod
    def normalize_score(cls, v) -> float:
        if v is not None and v > 1.0:
            v = v / 100.0
        return v


class LLMUserProfileModel(BaseModel):
    summary: Optional[str] = Field(
        default=None,
        description="Concise 2-3 sentence professional summary "
        "extracted from the resume. "
        "Should capture: current career stage, primary domain/industry, "
        "key strengths, and career trajectory. "
        "Example: 'Senior full-stack developer with 8 years "
        "of e-commerce experience, specializing in Python and React. "
        "Led teams of 5+ engineers and reduced infrastructure costs by 40%. "
        "Seeking technical leadership roles.'"
    )

    technical_skills: Optional[list[str]] = Field(
        default=None,
        description="Extract all hard/technical skills mentioned "
        "in the resume including: "
        "programming languages (Python, Java, SQL), "
        "frameworks (React, Django, Spring), "
        "tools (Docker, Kubernetes, Git), platforms "
        "(AWS, Azure, Salesforce), "
        "methodologies (Agile, Scrum, CI/CD), "
        "and software (Adobe, Excel, SAP). "
        "Exclude soft skills (leadership, communication) from this field. "
        "Each skill should be a single string. Example: "
        "['Python', 'AWS', 'TensorFlow', 'PostgreSQL', 'Git']"
    )

    first_experience_year: Optional[int] = Field(
        default=None,
        ge=1900,
        le=2326,
        description="Extract the calendar year (YYYY format)"
        " when the candidate's first professional work experience began. "
        "Look for the earliest start date across all work history entries, "
        "including full-time, part-time, internships, and contract roles. "
        "For freelance or self-employment, use the year of first paid project."
        " If exact month is provided, still extract only the year. "
        "If only month/year or season/year is available, extract the year. "
        "If ambiguous or no experience found, use null. "
        "Examples: 2015, 2020, 2008"
    )

    current_title: Optional[str] = Field(
        default=None,
        description="Extract the most recent job title exactly as written "
        "in the resume's latest work experience entry. "
        "Do not standardize or translate. If multiple current roles "
        "(e.g., freelancing while employed), "
        "prioritize the primary full-time position. "
        "If unemployed with recent title, use that. "
        "If unclear from context, use 'Not specified'. "
        "Example: 'Senior Software Engineer', "
        "'Product Manager III', 'Lead Data Scientist'"
    )

    title_history: Optional[list[str]] = Field(
        default=None,
        description="Extract all professional job titles from the "
        "candidate's work history in chronological "
        "order from earliest to most recent. "
        "Include exact titles as written without standardization. "
        "Include titles from full-time, part-time, contract, "
        "internship, and freelance roles. "
        "Exclude volunteer positions unless directly relevant "
        "professional experience. Each title should be a single string. "
        "If multiple roles at same company with different titles, "
        "include all distinct titles. "
        "Examples: ['Junior Developer', 'Software Engineer', "
        "'Senior Software Engineer', 'Tech Lead'] "
        "or ['Intern', 'Analyst', 'Associate', 'Manager']"
    )

    certifications: Optional[list[str]] = Field(
        default=None,
        description="Extract all professional certifications, "
        "licenses, and credentials including: "
        "full certification name, issuing body, and year if available."
        " Include both active and expired certifications. "
        "Exclude degrees, diplomas, and academic awards "
        "(those belong in education). "
        "Format as '[Certification Name] - [Issuing Body], "
        "[Year]' when possible. "
        "Example: ['PMP - Project Management Institute, 2021', "
        "'AWS Solutions Architect - Amazon, 2023', 'CFA Level II Candidate']"
    )

    @computed_field
    @property
    def years_of_experience(self) -> int | None:
        if self.first_experience_year is None:
            return None
        return date.today().year - self.first_experience_year
