FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen
COPY . .
CMD ["uv", "run", "python", "-c", "from dashboard.app import app; app.run(debug=False, host='0.0.0.0')"]