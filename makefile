.PHONY: help set-criteria find-new create-profile match-jobs dashboard

help:
	@echo "Available commands:"
	@echo "  make run    	 	- Run search"
	@echo "  make dashboard 	- Open dashboard"


run:
	@uv run python -c "from src.run import run; run()"

dashboard:
	@uv run python -c 'from dashboard.app import app; app.run(debug=True, host="0.0.0.0")'
