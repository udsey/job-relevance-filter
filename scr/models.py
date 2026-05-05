from typing import Literal, Optional

from pydantic import BaseModel, Field


class LinkedInJobsConfig(BaseModel):
    """Configuration model for LinkedIn Jobs API request."""

    url_search: Optional[str] = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    url_job: Optional[str] = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/"
    keywords: Optional[str] = Field(None, description="Job title or skill keywords")
    location: Optional[str] = Field(None, description="Geographic filter")
    max_reslts: int = Field(0, description="Max jobs to extract.")
    time_posted_interval: Optional[Literal["r86400", "r604800", "r2592000"]] = Field(None, description="Time posted filter: r86400 (24h), r604800 (week), r2592000 (month)")
    experience_level: Optional[Literal[1, 2, 3, 4, 5, 6]] = Field(None, description="Experience level: 1=Internship, 2=Entry, 3=Associate, 4=Mid-Senior, 5=Director, 6=Executive")
    job_type: Optional[Literal["F", "P", "C", "T", "I"]] = Field(None, description="Job type: F=Full-time, P=Part-time, C=Contract, T=Temporary, I=Internship")
    work_type: Optional[Literal[1, 2, 3]] = Field(None, description="Work type: 1=On-site, 2=Remote, 3=Hybrid")



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


    
    def __str__(self) -> str:
        return f"\n".join(f"{k}: {v}" for k, v in self.__dict__.items())