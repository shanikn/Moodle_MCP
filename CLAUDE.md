# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A read-only MCP server exposing a student's Reichman University Moodle (`moodle.runi.ac.il`) to Claude, via the same web-service API the Moodle mobile app uses (student token, no admin rights). README.md holds the planned tool roadmap (phases 1–4) and token setup; `docs/moodle_functions.md` lists every API function the student token can call — check it before assuming a `wsfunction` exists.

## Commands

Uses uv, Python 3.13+.

```
uv sync                                  # install deps (incl. dev: pytest, respx)
uv run moodle-mcp                        # run the MCP server (stdio)
uv run pytest                            # tests (none exist yet)
uv run pytest path/to/test.py::test_name # single test
```

Register with Claude Code: `claude mcp add moodle -- uv run --directory <repo> moodle-mcp`.

## Architecture

Layered: `server.py` (MCP tool definitions) → feature modules `assignments.py`, `courses.py`, `grades.py` (logic, shaping results) → `client.py` (`call()`) → `config.py` (per-year site + token). Shared shaping helpers (`fmt_date`, `html_to_text`, `file_list`, `browser_url`) live in `formatting.py`.

- **Per-year sites.** Each academic year is a separate Moodle site at `<MOODLE_BASE_URL>/<year>` with its own token. `config.py` collects every `MOODLE_TOKEN_<year>` env var; `get_site(year)` falls back to `MOODLE_DEFAULT_YEAR`. Every tool takes an optional `year` and threads it down to `call()`.
- **Config loads at import time.** `config.py` reads `.env` and requires `MOODLE_BASE_URL` and `MOODLE_DEFAULT_YEAR` on import — tests must set env vars before importing any `moodle_mcp` module.
- **`client.call(wsfunction, year=None, **params)`** POSTs to `/webservice/rest/server.php` with `moodlewssettingfilter=true` (applies Moodle text filters, so multilang course names come back in one language). Moodle reports errors as HTTP 200 with an `exception` key; `call()` turns those into `MoodleError`. List params are flattened to `key[0]`, `key[1]`, … as Moodle expects. Mock HTTP with `respx` (httpx is used directly).
- **Server** uses `mcp.server.mcpserver.MCPServer` (mcp ≥ 2.x, not the older `FastMCP` import). Tools are annotated `READ_ONLY`. Tool docstrings are what Claude sees as the tool description — keep them precise about return shape and cost.
- **Dates**: Moodle timestamps are Unix seconds, `0` = unset; `_date()` formats them as local `"YYYY-MM-DD HH:MM"` or `None`.
- **Per-item API calls** (e.g. submission status per assignment) run in a `ThreadPoolExecutor(max_workers=8)`.
- **Local state**: Moodle has no "created" timestamp, so `new_assignments` keeps first-seen times in `.state/seen_assignments_<year>.json` (git-ignored, repo root). The first run only records a baseline.
