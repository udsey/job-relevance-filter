.PHONY: help set-criteria find-new create-profile match-jobs dashboard

help:
	@echo "Available commands:"
	@echo "  make run          - Run the job relevance search"
	@echo "  make dashboard    - Open the dashboard UI"
	@echo "  make docker-up    - Start Docker containers (build, detached)"
	@echo "  make docker-logs  - Follow Docker container logs"
	@echo "  make docker-down  - Stop Docker containers"


run:
	@uv run python -c "from src.run import run; run()"

dashboard:
	@uv run python -c 'from dashboard.app import app; app.run(debug=True, host="0.0.0.0")'

docker-up:
	@docker compose up --build -d

docker-logs:
	@docker compose logs -f

docker-down:
	@docker compose down