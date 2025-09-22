# Repository Guidelines

## Project Structure & Module Organization
Source lives in `src/claude_sdk_server`, with FastAPI routers under `api/routers`, service logic in `services`, streaming helpers in `streaming`, and shared utilities (including logging) in `utils`. Tests belong in `tests/`, mirroring package paths (e.g., `tests/test_logging_config.py`). Legacy assets are archived in `legacy/`; do not modify them unless migrating code back into `src/`.

## Build, Test, and Development Commands
Use Docker via `make up` to build and start the API, `make down` to stop, and `make restart` for quick rebuilds. Tail logs with `make logs` or filter structured output with `make logs-pretty`. Launch the React dashboard when needed with `make frontend-3002`. For smoke checks, hit `/api/v1/query/stream` directly with the curl recipe in the README; there is no standalone `/health` route.

## Coding Style & Naming Conventions
Target Python 3.13 with 4-space indentation, descriptive type hints, and snake_case modules. Imports are auto-organized and linted by Ruff; run `ruff check .` before opening a PR if you touch formatting-sensitive code. Keep router, service, and model names aligned with their API responsibilities (e.g., `claude_router.py`, `claude_service.py`). Configuration constants live alongside their module unless shared, in which case place them in `utils/`.

## Testing Guidelines
Tests use `pytest` and live beside the feature they cover (e.g., `tests/test_logging_config.py`). Name new test classes `Test<ThingUnderTest>` and structure fixtures close to usage. Run `uv run pytest` before opening a PR and manually exercise streaming flows with the curl example—automation is intentionally minimal.

## Commit & Pull Request Guidelines
Recent commits follow short, imperative summaries (`Update atla config`, `Add file route ...`). Match that tone, scope each commit narrowly, and include context in the body when altering API contracts. Pull requests should explain the change, list impacted endpoints or services, and mention test commands executed; attach screenshots or logs for streaming/UI tweaks. Link tracking issues with `Fixes #123` when applicable.

## Environment & Configuration Tips
Copy `.env.example` to `.env` and supply real credentials before starting the stack—`ANTHROPIC_API_KEY`, `ATLA_INSIGHTS_API_KEY`, `ATLA_ENVIRONMENT`, and `LOGFIRE_TOKEN` are all mandatory. Docker Compose picks up the file automatically. When debugging locally, hit `http://localhost:8000/api/v1/query/stream` with the README curl recipe to validate SSE output before handing changes to the frontend.
