# Repository Guidelines

## Project Structure & Module Organization

- `cli.py` orchestrates the lead flow: search → details → website fetch → analysis → CSV export.
- Core package `leadgen/`: `places.py` (Google Places search/details), `website_fetch.py` (HTTP fetch with UA + timeout), `analysis.py` (HTML heuristics), `export.py` (CSV writer), `models.py` (dataclasses), `config.py` (env loading), `ai_scoring.py` (placeholder).
- Data lives under `data/`: drop sample HTML in `data/sample_html/`; CSV outputs default to `data/outputs/`.
- Tests belong in `tests/` using `pytest`; mirror module names (e.g., `test_analysis.py`, `test_places.py`).

## Setup, Build & Run

- Requirements: Python 3.10+ and a `.env` with `GOOGLE_API_KEY` (required), optional `OPENAI_API_KEY`/`GEMINI_API_KEY` for future AI scoring.
- Install deps from the repo root:
  ```bash
  python -m venv .venv && source .venv/bin/activate
  pip install -r leadgen/requirements.txt
  ```
- Run the CLI locally (writes CSV to `data/outputs/`):
  ```bash
  python cli.py -q "coffee shops in Austin" -o data/outputs/leads.csv --limit 15
  ```
- API calls hit Google; respect quotas and keep keys in `.env` (never commit secrets).

## Coding Style & Naming Conventions

- Follow PEP 8 with 4-space indents; prefer explicit type hints (`str | None`) and dataclasses for data carriers.
- Keep functions small and side-effect aware; handle HTTP/API errors explicitly instead of silent `except Exception`.
- Use snake_case for functions/variables, PascalCase for dataclasses, and descriptive module names aligned with responsibilities.

## Testing Guidelines

- Use `pytest`; name tests `test_*.py` and group by module. Place HTML fixtures under `data/sample_html/` and mock HTTP/Google calls to avoid hitting external services.
- Cover edge cases noted in diagnostics: empty results in `export_csv`, API error handling in `places.py`, URL validation/timeouts in `website_fetch.py`, and heuristic accuracy in `analysis.py`.

## Commit & Pull Request Guidelines

- Write imperative, specific commit subjects ("Add export guard for empty results") with concise bodies summarizing rationale and tests run.
- For PRs: include a short description, reproduction/verification steps (sample CLI command), linked issues if any, and note any config/env changes. Add screenshots of CLI output if it aids reviewers.

## Security & Configuration Tips

- Keep `.env` out of version control; rotate keys if exposed. Avoid logging secrets or full API responses.
- When adding new integrations, prefer configurable timeouts/retries and document any new env vars in this guide.

# Codex Agent Instructions for `~/leads`

You are an AI coding agent working on a Python project: a lead generation bot that:

- uses the Google Places / Maps APIs to find businesses,
- fetches their websites,
- analyzes site quality (modern vs outdated, chatbot, AI presence),
- exports results to CSV (and later Google Sheets).

## Global Rules

- Always assume **Test-Driven Development (TDD)**:
  1. Prefer to create or extend tests first.
  2. Then modify implementation code so tests pass.
  3. Then refactor while keeping tests green.
- Before making changes, read `DIAGNOSTIC_REPORT.md` in the project root. Treat it as the main spec.
- Respect the existing module boundaries:
  - `leadgen/places.py` → Google Places integration
  - `leadgen/website_fetch.py` → HTTP fetching
  - `leadgen/analysis.py` → rule-based HTML analysis
  - `leadgen/export.py` → CSV export
  - `leadgen/models.py` → data models
  - `cli.py` → CLI entry point

## When the user asks to "fix" or "add" something

1. Look for or create tests under `tests/` that describe the desired behavior.
2. Make minimal changes to the implementation to satisfy those tests.
3. Avoid rewriting entire files unless explicitly requested.
4. Use clear, small commits: group related changes together.

## Safety and Environment

- Assume this is running in WSL Ubuntu with a Python virtualenv in `.venv`.
- Do not add hard-coded secrets. All keys come from environment variables and `.env` via `leadgen/config.py`.
- If you are unsure, propose a small plan in comments or markdown before large changes.

## Reporting

- When `/review` is run, summarize:
  - Any failing tests and likely causes.
  - Any obvious architectural issues or smells.
  - Suggestions for new tests based on `DIAGNOSTIC_REPORT.md`.
