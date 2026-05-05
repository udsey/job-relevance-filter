.PHONY: help set-criteria find-new create-profile match-jobs

help:
	@echo "Available commands:"
	@echo "  set-criteria    - Create search criteria"
	@echo "  find-new        - Find new jobs"
	@echo "  create-profile  - Create user profile"
	@echo "  match-jobs      - Match jobs to profile"

set-criteria:
	@uv run python -c "from scr.utils import create_search_criteria; create_search_criteria()"

find-new:
	@uv run python -c"from scr.scraper import find_new_jobs; find_new_jobs()"

create-profile:
	@uv run python -c "from scr.utils import create_user_profile; create_user_profile()"

match-jobs:
	@uv run python -c "from scr.utils import match_jobs; match_jobs()"
