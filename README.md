# Job Relevance Filter

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=fff" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/LangChain-1c3c3c?logo=langchain&logoColor=white" alt="LangChain">
  <img src="https://img.shields.io/badge/Ollama-000000?logo=ollama&logoColor=fff" alt="Ollama">
  <img src="https://img.shields.io/badge/Groq-00AA00?logo=groq&logoColor=fff" alt="Groq">
  <img src="https://img.shields.io/badge/DeepSeek-4A6CF7?&logoColor=fff" alt="DeepSeek">
  <img src="https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=fff" alt="Pydantic">
  <img src="https://img.shields.io/badge/Dash-008DE4?logo=plotly&logoColor=fff" alt="Dash">
  <img src="https://img.shields.io/badge/BeautifulSoup-4-43B02A?logoColor=fff" alt="BeautifulSoup">
  <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=fff" alt="Docker">
</p>

A Dash-based job search dashboard that scrapes LinkedIn (via its guest API), uses an LLM to
match postings against your CV, and lets you manage the entire workflow from a single UI.

---

## Features

- 📊 **Dashboard-first workflow** — all operations (search, review, match, track) are
  performed through a browser-based Dash application
- 🔍 **LinkedIn scraping** — calls LinkedIn's guest jobs API, parses HTML with BeautifulSoup
  across keyword + location combinations defined in search criteria
- 📄 **CV parsing** — extracts a structured profile from your PDF resume using `pdfplumber`
  + an LLM, stored as `configs/profile.yaml`
- 🤖 **LLM job matching** — LangChain-powered agent that evaluates each job against your
  profile and returns a relevance score (0.0–1.0), confidence level, matching skills,
  missing requirements, and a recommendation
- 📋 **Card-based review queue** — one-at-a-time job cards where you accept, skip, or
  remove jobs; accepted jobs move to tracking
- 🎯 **On-demand matching** — paste any job description for an instant relevance score
  against your profile
- 📈 **Application tracking** — Kanban board with drag-through stages
  (Applied → Screened → Interview → Offered), Sankey funnel diagram, and per-application notes
- 🏷️ **Tag-based profile editing** — add/remove skills, job titles, certifications,
  and search criteria as interactive tags
- ⚙️ **Flexible LLM backend** — supports local Ollama models, Groq API, or DeepSeek API
- ⏰ **Scheduled scraping** — configurable cron-based auto-scraping via APScheduler,
  with a catch-up run if today's schedule was missed
- 🚀 **Run pipeline on demand** — trigger the find-and-match pipeline from the dashboard
  Overview page with a single click
- 📉 **Rich analytics** — KPI cards, trend charts, score distributions, company breakdowns,
  seniority/employment type breakdowns, and Sankey funnel analytics
- 🔌 **Firefox Extension API** — REST endpoints consumed by the
  [companion LinkedIn Extension](https://github.com/udsey/linkedin-extension) for
  auto-syncing applied jobs and on-page matching
- 🐳 **Docker support** — run the full stack with a single command

## Requirements

- **Python** 3.11 or later
- **Ollama** (optional, for local LLM inference) — [install guide](https://ollama.ai/download)
- **Groq API key** (optional) — [get one here](https://console.groq.com)
- **DeepSeek API key** (optional) — [get one here](https://platform.deepseek.com)
- **Docker & Docker Compose** (optional, for containerized deployment)

## Installation

```bash
git clone https://github.com/udsey/job-relevance-filter.git
cd job-relevance-filter

# Install uv (if not installed)
pip install uv

# Create virtual environment and install dependencies
uv sync
```

Optional — set API keys for cloud LLM providers:

```bash
# .env
GROQ_API_KEY=your_groq_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

> No API keys needed if using a local Ollama model.

## Usage

### Dashboard (primary interface)

Launch the dashboard to manage your job search from a single UI:

```bash
make dashboard
```

Opens at `http://localhost:8050`. The dashboard starts a background scheduler that
automatically runs the find-and-match pipeline on a cron schedule.

#### Pages

| Page | Route | Description |
|---|---|---|
| **Overview** | `/` | KPI cards, trend charts, score distributions, company/seniority breakdowns, filterable job table, and a "Run now" button to trigger the pipeline ad-hoc |
| **Jobs** | `/jobs` | One-at-a-time job review with accept / skip / remove actions |
| **Job Tracker** | `/jobs-tracker` | Kanban board (Applied → Screened → Interview → Offered), Sankey funnel chart, per-job notes, manual job addition, and a filterable table |
| **Match Job** | `/match-job` | Paste a job description and get an instant relevance score, matching skills, missing requirements, and summary |
| **Criteria & Profile** | `/profile` | Search criteria form (keyword, location, time posted, experience level, job type, work type), LLM-powered profile extraction from PDF upload, and tag-based profile editing |

### Firefox Extension integration

The dashboard provides a REST API consumed by the
[LinkedIn Job Tracker Extension](https://github.com/udsey/linkedin-extension)
— a Firefox WebExtension that scrapes LinkedIn job postings, listens for job applications,
and matches jobs against your CV from within the browser.

| Endpoint | Method | Used by extension | Description |
|---|---|---|---|
| `/api/last-sync` | GET | `background.js`, `utils.js` | Returns the last sync timestamp; the extension uses this to decide whether a daily sync is needed |
| `/api/sync-jobs` | POST | `sync_apply.js`, `sync_applied.js` | Syncs job postings, deduplicating by `job_id` |
| `/api/match-job` | POST | `match_job.js` | Matches a job description against your profile; returns scoring, matching skills, missing requirements, and summary |

### Other commands

| Command | Description |
|---|---|
| `make dashboard` | Launch the interactive dashboard |
| `make run` | Run the full find-and-match pipeline headlessly (no scheduler, no UI) |
| `make docker-up` | Start all services with Docker Compose (build, detached) |
| `make docker-logs` | Follow container logs |
| `make docker-down` | Stop all containers |

## Configuration

Configuration files live in the `configs/` directory.

### `configs/config.yaml`

```yaml
max_results: 25                # Max jobs to fetch per search
cron: "0 9 * * *"              # Cron schedule for auto-scraping
relevance_threshold: 0.65      # Minimum score to consider a match
no_response_days: 14           # Days before flagging no-response
llm_config:
  model_type: deepseek         # "local", "groq", or "deepseek"
  model_name: deepseek-v4-flash
  temperature: 0.2
```

### `configs/criteria.yaml`

Search parameters for LinkedIn scraping (managed via the dashboard):

```yaml
search_parameters:
  - keywords: "python developer"
    geo_id: "103644278"        # United States
    time_posted_interval: "r86400"
    experience_level: null
    job_type: null
    work_type: null
```

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | For Groq | API key for Groq cloud LLM |
| `DEEPSEEK_API_KEY` | For DeepSeek | API key for DeepSeek cloud LLM |

## Output

Results are saved to `data/jobs.csv` with the following columns:

| Column | Description |
|---|---|
| `job_id` | LinkedIn job ID |
| `job_title` | Job title from the listing |
| `company` | Company name |
| `location` | Job location |
| `job_url` | Link to the LinkedIn posting |
| `posted_time` | When the job was posted |
| `description` | Full job description |
| `seniority` | Seniority level |
| `employment_type` | Full-time, part-time, contract, etc. |
| `easy_apply` | Whether LinkedIn Easy Apply is available |
| `job_summary` | LLM-generated concise summary |
| `relevance_score` | 0.0–1.0 fit score |
| `confidence_level` | LLM certainty in the assessment |
| `reason` | Detailed explanation of the match |
| `matching_skills` | Skills from your profile that match |
| `missing_requirements` | Gaps identified |
| `recommendation` | INTERVIEW / CONSIDER / REJECT / NEED_MORE_INFO |
| `status` | `new`, `seen`, `removed`, `applied`, etc. |
| `applied_at` / `screened_at` / `interview_at` / `offered_at` / `rejected_at` | Stage timestamps |
| `notes` | Free-text notes per application |
| `created_at` | Timestamp when the match was created |

## Docker

```bash
make docker-up       # Build & start
make docker-logs     # Follow logs
make docker-down     # Stop
```

## Project structure

```
├── configs/            # YAML configuration files (config.yaml, criteria.yaml, profile.yaml)
├── dashboard/          # Dash web application (primary interface)
│   ├── app.py          # App entry point, layout, navbar, API routes, scheduler init
│   ├── assets/         # Static assets (CSS, JS, images, favicon)
│   ├── components/     # Reusable UI components (KPI cards, utilities)
│   ├── pages/          # Page layouts (Overview, Jobs, Job Tracker, Match Job, Profile)
│   └── static/         # Static images (empty states)
├── data/               # Output data (jobs.csv)
├── src/                # Core library (imported and orchestrated by the dashboard)
│   ├── run.py          # Pipeline orchestration: scrape → summarise → match → save
│   ├── scraper.py      # LinkedIn guest API scraping via requests + BeautifulSoup
│   ├── parser.py       # LLM-based job matching, summary extraction, and profile extraction
│   ├── models.py       # Pydantic data models for configs, jobs, matches, profiles
│   ├── scheduler.py    # APScheduler-based cron runner with catch-up logic
│   ├── setup.py        # Config loading, directory setup, logging init
│   └── utils.py        # YAML i/o helpers and path checks
├── Dockerfile          # Container build
├── docker-compose.yml  # Multi-service setup
└── makefile            # Convenience targets (dashboard, run, docker-*)