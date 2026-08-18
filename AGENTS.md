# AGENTS.md — JARVIS / HEER

## Project
HEER (AI Agency Operating Partner) is a Python 3.14 stdlib-only HTTP server (`agent/main.py`) serving a vanilla JS SPA (`ui/`). No web framework, no build step, no migrations.

## Commands
- `python3 -m unittest discover -s tests -p '*_test.py'` — run all 346 tests.
- `python3 -m unittest tests.task_graph_test -v` — single test module.
- `python3 -m unittest tests.task_graph_test.TaskGraphDagTests.test_diamond_dag_valid_and_deterministic -v` — single test.
- `python3 tests/task_graph_test.py` — single file directly.
- `python3 -m agent.main` — start server (`127.0.0.1:8000`, override with `HEER_PORT`).
- `python3 -m agent.orchestrator --self-test` — canned routing/approval self-test.
- `python3 scripts/acceptance_phase32.py [base_url]` — live-server acceptance tests.
- `python3 scripts/verify_skills.py` — verify JARVIS skills integration.

## Architecture
- `agent/main.py` — stdlib `ThreadingHTTPServer`; every API endpoint lives here.
- `agent/chat.py` — deterministic intent router + optional LLM hook.
- `agent/orchestrator.py` — route → plan → approve → execute → verify → audit.
- `agent/registry.py` — executable agent + tool registry (approval levels 0–3).
- `agent/heer.py` — 15 fixture agents (dashboard data only, not executable) + intelligence payloads.
- `agent/vault.py` — markdown knowledge graph (nodes/links).
- `agent/data.py` — **single gateway** for data roots, env loading, and demo mode.
- `agent/business.py` — business registry backed by `businesses.json`.
- `agent/mission_engine.py`, `agent/task_graph.py`, `agent/execution_engine.py` — mission/DAG/parallel execution layer.
- `ui/` — vanilla JS SPA (`index.html`, `app.js`, `style.css`), no bundler.

## Data & Env
- `agent/data.py` parses `.env` itself (no python-dotenv). Keys: `HEER_DEMO`, `INDEX_PATHS`, `EDGE_TTS_VOICE`, `ELEVENLABS_API_KEY`, `OPENAI_API_KEY`.
- Default is **demo mode** (`HEER_DEMO=1`); never indexes real folders unless explicitly configured.
- Business definitions in `businesses.json`; default is `ai_agency` → `data/demo/`.
- SQLite learning DB at `memory/skills.db` (auto-created).

## Testing Quirks
- `agent/` has no `__init__.py`; relative imports are used internally.
- Tests inject repo root into `sys.path` and import `from agent import xxx`.
- No pytest fixtures or conftest.py; tests are pure `unittest`.
- Acceptance scripts require a live server; unit tests do not.

## Style / Workflow
- No `pyproject.toml`, no Makefile, no CI, no linter, no typechecker configured.
- Python 3.14+ required.
- Keep new modules stdlib-only unless they touch existing non-stdlib deps (`dotenv`, `@elevenlabs/elevenlabs-js`).
