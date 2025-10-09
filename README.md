# NBA API

FastAPI service that aggregates NBA live game data and player stats with async fetches, caching, and retry logic. The project is structured into presentation, use case, domain, and services layers to keep responsibilities clear.

## Requirements

- Python 3.12+
- Poetry 1.8+
- Docker (optional, for containerized runs)

## Getting Started

### Non-Docker workflow

```bash
poetry install
poetry run uvicorn nba_api.main:app --host 0.0.0.0 --port 8000 --reload
```

Open <http://localhost:8000/> for the scoreboard and <http://localhost:8000/players-stats> for player stats. The `/refresh` and `/players-stats/refresh` endpoints trigger background cache updates.

To run without Poetry, install dependencies and start uvicorn manually:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt  # or `pip install .` if packaged
uvicorn nba_api.main:app --host 0.0.0.0 --port 8000
```

## Running Tests & Linters

```bash
poetry run pytest
poetry run ruff check src tests
poetry run mypy src tests
```

## Docker

Build and run with Docker Compose:

```bash
docker compose build --pull
docker compose up
```

The API is exposed on `http://localhost:8018`. The container includes health checks and runs as a non-root user.

## Project Layout

- `src/nba_api/presentation`: FastAPI app wiring, routing, and state management
- `src/nba_api/use_cases`: Application orchestration (scoreboard, players)
- `src/nba_api/services`: HTTP client and NBA API integration
- `src/nba_api/domain`: Parsing helpers and domain enums
- `tests/`: coverage for services, parsers, state, routes, and use cases
