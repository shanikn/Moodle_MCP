# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A read-only MCP server exposing a student's Reichman University Moodle (`moodle.runi.ac.il`) to Claude, via the same web-service API the Moodle mobile app uses (student token, no admin rights). `exam_schedule` instead scrapes Yedion (`yedion.runi.ac.il`, the student info station), logged in with the student's university password through My RUNI single sign-on. README.md holds the planned tool roadmap (phases 1–4) and token setup; `docs/moodle_functions.md` lists every API function the student token can call — check it before assuming a `wsfunction` exists.

## Commands

Uses uv, Python 3.13+.

```
uv sync                                  # install deps (incl. dev: pytest, respx)
uv run moodle-mcp                        # run the MCP server (stdio)
uv run pytest                            # tests (mocked Moodle, no network; ~1 s)
uv run pytest path/to/test.py::test_name # single test
```

Register with Claude Code: `claude mcp add moodle -- uv run --directory <repo> moodle-mcp`.

## Architecture

Layered: `server.py` (MCP tool definitions) → feature modules `assignments.py`, `exams.py` (Yedion, via `runi.py`), `courses.py`, `grades.py`, `messages.py`, `deadlines.py`, `calendar.py`, `search.py`, `reading.py` (logic, shaping results) → `client.py` (`call()`) → `config.py` (per-year site + token). Shared shaping helpers (`fmt_date`, `html_to_text`, `file_list`, `browser_url`) live in `formatting.py`.

- **Per-year sites.** Each academic year is a separate Moodle site at `<MOODLE_BASE_URL>/<year>` with its own token. `config.py` collects every `MOODLE_TOKEN_<year>` env var; `get_site(year)` falls back to `MOODLE_DEFAULT_YEAR`. Every tool takes an optional `year` and threads it down to `call()`.
- **Config loads at import time.** `config.py` reads `.env` and requires `MOODLE_BASE_URL` and `MOODLE_DEFAULT_YEAR` on import — tests must set env vars before importing any `moodle_mcp` module.
- **`client.call(wsfunction, year=None, **params)`** POSTs to `/webservice/rest/server.php` with `moodlewssettingfilter=true` (applies Moodle text filters, so multilang course names come back in one language). Moodle reports errors as HTTP 200 with an `exception` key; `call()` turns those into `MoodleError`. List params are flattened to `key[0]`, `key[1]`, … as Moodle expects. Mock HTTP with `respx` (httpx is used directly).
- **Server** uses `mcp.server.mcpserver.MCPServer` (mcp ≥ 2.x, not the older `FastMCP` import). Register tools with the `@tool` decorator in `server.py`, not `@mcp.tool` directly: it marks them read-only and converts `MoodleError`, `RuniError`, `ValueError` and `httpx.HTTPError` into `ToolError`. mcp hides the message of any other exception (Claude only sees "Error executing tool"), so raise `ValueError` with a helpful message for bad input. Tools return a dict, never a bare list (mcp sends a list as one content block per item): wrap lists as e.g. `{"courses": [...]}`. Tool docstrings are what Claude sees as the tool description — keep them precise about return shape and cost.
- **Dates**: Moodle timestamps are Unix seconds, `0` = unset; `formatting.fmt_date()` formats them as local `"YYYY-MM-DD HH:MM"` or `None`.
- **Per-item API calls** run in a `ThreadPoolExecutor` (8 workers for submission status, 4 in `messages.py`: the university server returned 502s under heavier parallel load). `call()` retries once on HTTP 5xx.
- **Reading files** (`reading.py`): browser file links are rewritten to `webservice/pluginfile.php` and fetched with the token as a query param. The token is only sent when the URL starts with a configured year's site URL (`_site_year`); keep that check. Text is extracted with `pypdf` (PDF), `python-pptx`, `python-docx`, and from `.ipynb` JSON (served as `application/json`, so only JSON with an `error` key is a Moodle error). Moodle reports file errors as HTTP 200 JSON `{"error": ...}`.
- **Yedion** (`runi.py`, `exams.py`): `runi.fetch(prgname, arguments, **fields)` POSTs to `fireflyweb.aspx` (Yedion menu buttons carry `data-progname` / `data-arguments`; a form submit also sends the page's form fields, e.g. `TZ` and `Token`) and returns the HTML. Login chain: My RUNI F5 form (`/my.policy`, `RUNI_USERNAME` / `RUNI_PASSWORD`) → `yedion/login.aspx?Type=S` → SAML IdP at `auth.runi.ac.il` → POST the `SAMLResponse` form to Yedion. A page is logged in iff it has `id="ExitStudent"`. Rules, all tested: login lazily under a `threading.Lock`; on an expired session re-login at most once per call, and only one thread re-logs in (generation counter); a refused password or any unexpected login page (MFA, block) is remembered and never retried until restart (account lockout); the `SAMLResponse` is only posted to Yedion. The password, F5 cookies, `SAMLResponse`, SSO URLs and the student id (`TZ`) identify the student: never log them or put them in error messages (`RuniError` messages give host + path only; httpx errors are reduced to their type). Don't send `Accept: application/json` / `X-Requested-With` on the login requests: My RUNI then answers 502. Parse Yedion pages by the real Hebrew strings (the terminal shows RTL text reversed). Exam results are a `div.row` / `div.col` grid, columns found by header text (the semester column only appears for the whole year); "אין מידע ליצירת תוכנית בחינות" means no exams. Test pages in `tests/fixtures/` are anonymized.
- **Local state**: Moodle has no "created" timestamp, so `new_assignments` keeps first-seen times in `.state/seen_assignments_<year>.json` (git-ignored, repo root). The first run only records a baseline.

## Tests

`tests/conftest.py` sets fake env vars and disables `load_dotenv` before importing `moodle_mcp`, so tests never see the real tokens or password. The `runi_site` fixture is a fake My RUNI + Yedion (respx, cookie sessions): set `runi_site.pages[PRGNAME]`, inspect `runi_site.posts` / `password_posts`, call `runi_site.expire()`, or set `accepted_password` / `after_password = "mfa"` for login failures. The `moodle` fixture is a fake web-service endpoint (respx): register answers with `moodle.on(wsfunction, json_or_callable)` and inspect requests with `moodle.calls_to(wsfunction)`; any unmocked request fails the test. If `uv run` fails with "file is being used by another process", the MCP server is running in Claude Code; use `uv run --no-sync pytest`.

`client.py` uses one shared `httpx.Client` — creating a client per request (e.g. `httpx.post`) costs ~0.3 s each on Windows for SSL setup.
