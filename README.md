# linkedin-job-matcher

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff" alt="Python">
  <img src="https://img.shields.io/badge/LangChain-1c3c3c?logo=langchain&logoColor=white" alt="LangChain">
  <img src="https://img.shields.io/badge/Ollama-000000?logo=ollama&logoColor=fff" alt="Ollama">
  <img src="https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=fff" alt="Pydantic">
    <img src="https://img.shields.io/badge/Requests-2CA5E0?logo=python&logoColor=fff" alt="Requests">
    <img src="https://img.shields.io/badge/BeautifulSoup-4-43B02A?logoColor=fff" alt="BeautifulSoup">
</p>

**linkedin-job-matcher** is an autonomous job search assistant that scrapes LinkedIn for job postings and uses an LLM to match them against your CV — scoring each role by relevance, confidence, and fit.

Configure your search criteria, upload your CV, and let the agent do the rest: it finds new listings, enriches them with full job details, and produces a ranked CSV ready for review.

## Features

- 🔍 **Scrapes LinkedIn Jobs** across multiple keyword + location combinations
- 📄 **Extracts your profile** from a PDF CV using an LLM
- 🤖 **Matches jobs to your profile** with relevance score, confidence level, and reasoning
- ⚙️ **Flexible LLM backend** — supports local Ollama models or Groq API

## Quickstart

```bash

# 1. Extract your profile from your CV
make create-profile

# 2. Set search criteria (keywords, locations, filters)
make set-criteria

# 3. Scrape new LinkedIn job postings
make find-new

# 4. Match jobs against your profile
make match-jobs
```

## Configuration

On first run, a `config.yaml` is created in the project root. You can also edit it directly:

```yaml
max_results: 25
llm_config:
  model_type: groq         # "groq" or "local"
  model_name: llama3-8b-8192
  temperature: 0.0
  match_job_prompt: "..."
  extract_user_profile_prompt: "..."
search_parameters: []      # Populated via make set-criteria
```

For Groq, set your API key:

```bash
export GROQ_API_KEY=your_key_here
```

## Output

Results are saved to `data/jobs.csv` with the following match columns appended per job:

| Column | Description |
|---|---|
| `relevance_score` | 0.0–1.0 fit score |
| `confidence_level` | LLM certainty in the assessment |
| `reason` | Detailed explanation |
| `matching_skills` | Skills from your profile that match |
| `missing_requirements` | Gaps identified |
| `recommendation` | Suggested next step |