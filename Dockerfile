FROM python:3.13.0-slim-bookworm

ENV POETRY_VERSION=1.8.3 \
  POETRY_VIRTUALENVS_IN_PROJECT=true \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

RUN apt-get update \
  && apt-get dist-upgrade -y \
  && apt-get install -y --no-install-recommends curl \
  && pip install --no-cache-dir "poetry==${POETRY_VERSION}" \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock* README.md ./

RUN poetry install --no-interaction --no-ansi --no-root

COPY . .

RUN poetry install --no-interaction --no-ansi

RUN useradd --create-home app \
  && chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

CMD ["poetry", "run", "uvicorn", "nba_api.main:app", "--host", "0.0.0.0", "--port", "8000"]