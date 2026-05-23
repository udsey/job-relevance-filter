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

An autonomous job search assistant that scrapes LinkedIn for job postings and uses an LLM to match them against your CV — scoring each role by relevance, confidence, and fit. All operations are managed through an interactive Dash dashboard.

---

## Features

- 📊 **Interactive Dashboard** — browser-based UI for managing your entire job search
- 🔍 **Scrapes LinkedIn Jobs** across multiple keyword + location combinations
- 📄 **Extracts your profile** from a PDF CV using an LLM
- 🤖 **Matches jobs to your profile** with relevance score, confidence level, and reasoning
- ⚙️ **Flexible LLM backend** — supports local Ollama models, Groq API, or DeepSeek API
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

Opens at `http://localhost:8050`. From the dashboard you can:

- **Overview** — KPI cards, charts, and data table of all jobs
- **Jobs** — one-at-a-time job review with accept / skip / remove
- **Profile** — search criteria form and LLM-powered profile extraction from PDF
- **Tracking** — Kanban board and funnel chart to manage applications

### Other commands

| Command | Description |
|---|---|
| `make run` | Run the full find-and-match pipeline headlessly |
| `make dashboard` | Launch the interactive dashboard |
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

Results are saved to `data/jobs.csv` with the following match columns:

| Column | Description |
|---|---|
| `relevance_score` | 0.0–1.0 fit score |
| `confidence_level` | LLM certainty in the assessment |
| `reason` | Detailed explanation |
| `matching_skills` | Skills from your profile that match |
| `missing_requirements` | Gaps identified |
| `recommendation` | Suggested next step |
| `job_summary` | Concise human-friendly job summary |
| `status` | `new`, `applied`, `interviewing`, etc. |
| `created_at` | Timestamp when the match was created |

## Docker

```bash
make docker-up       # Build & start
make docker-logs     # Follow logs
make docker-down     # Stop
```

## Project structure

```
├── configs/            # YAML configuration files
├── dashboard/          # Dash web application (primary UI)
│   ├── app.py          # App entry point
│   ├── components/     # Reusable UI components
│   └── pages/          # Page layouts
├── data/               # Output data (jobs.csv)
├── src/                # Core application code
│   ├── run.py          # Main pipeline orchestration
│   ├── scraper.py      # LinkedIn job scraping
│   ├── parser.py       # LLM-based job matching & profile extraction
│   ├── models.py       # Pydantic data models
│   ├── scheduler.py    # Cron-based job scheduler
│   ├── setup.py        # Config loading & initialization
│   └── utils.py        # Utility functions
├── Dockerfile          # Container build
├── docker-compose.yml  # Multi-service setup
└── makefile            # Convenience targets
```