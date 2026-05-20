.PHONY: help set-criteria find-new create-profile match-jobs dashboard

find-new:
	@uv run python -c"from src.scraper import find_new_jobs; find_new_jobs()"

create-profile:
	@uv run python -c "from src.utils import create_user_profile; create_user_profile()"

match-jobs:
	@uv run python -c "from src.utils import match_jobs; match_jobs()"

find-and-match: find-new match-jobs


dashboard:
	@uv run python -c 'from dashboard.app import app; app.run(debug=True, host="0.0.0.0")'
