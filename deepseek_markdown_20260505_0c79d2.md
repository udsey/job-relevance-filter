# Project Definition: Automated Job Filtering & Field Extraction

## Project Name (Git Repo)
`job-relevance-filter`

## Reference
[How to Scrape LinkedIn Job Listings in 2026 (Python, Public API, No Login Required)](https://dev.to/agenthustler/how-to-scrape-linkedin-job-listings-in-2026-python-public-api-no-login-required-5bin#comments)

## 1. Purpose
Automate job search filtering using a local LLM. Classify jobs as relevant/irrelevant and extract structured fields. Zero cost. For personal use only.

## 2. Input
- **Source:** `config.yaml` (user-defined job search parameters: keywords, location, filters)
- **Platform:** LinkedIn (guest API first, fallback to Selenium if needed)

## 3. Output
**CSV file** with columns:
- `job_title`
- `company`
- `location`
- `url`
- `date_posted`
- `is_relevant` (true/false)
- `relevance_reason` (short LLM explanation)
- `extracted_skills` (comma-separated)
- `raw_text` (original job description snippet)

All jobs saved to single CSV with `is_relevant` flag.

## 4. Processing Flow
1. Read `config.yaml`
2. Scrape LinkedIn job listings (`requests` + guest API per reference article)
3. For each job:
   - Send job title + description to LLM
   - Receive: `{relevant: bool, fields: {...}, reason: string}`
4. Append to CSV
5. Optional deduplication (check URL against existing entries)

## 5. LLM Configuration

**Order of models to try (stop when satisfactory):**

| Order | Model | Ollama Command | Notes |
|-------|-------|----------------|-------|
| 1 | Llama 3.2 3B | `ollama pull llama3.2:3b` | Fast, stable, fits 4GB VRAM |
| 2 | Llama 3 (8B) | `ollama pull llama3:latest` | Slower, better accuracy |
| 3 | Qwen2.5 7B | `ollama pull qwen2.5:7b` | Fallback only |

**Hardware:** NVIDIA GTX 1650 (4GB VRAM), 7.5GB RAM

## 6. Technologies
- **Scraping:** `requests` + BeautifulSoup (guest API), fallback to Selenium
- **LLM:** Ollama (local)
- **Output:** CSV via `pandas` or `csv` module
- **Config:** PyYAML

## 7. Constraints
- Budget: $0
- Runtime acceptable (overnight/batch processing)
- English language only