# Moodle MCP

An MCP server that gives Claude read access to a student's Moodle account
(Reichman University, `moodle.runi.ac.il`), using the same web-service API as the Moodle mobile app.
No admin rights needed.

> **Status:** work in progress. Config is done; the API client and tools are being built.

## Planned tools

| Tool | Description |
|---|---|
| `list_assignments` | All assignments across your courses, with due dates |
| `new_assignments` | Assignments added (or updated) since the last check / today |

Every tool takes an optional `year` (defaults to `MOODLE_DEFAULT_YEAR`).
All API functions available to a student token: [docs/moodle_functions.md](docs/moodle_functions.md).

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.13+.

```
uv sync
```

Create `.env` in the project root (it is git-ignored):

```
MOODLE_BASE_URL=https://moodle.runi.ac.il
MOODLE_TOKEN_2026=<token>
MOODLE_TOKEN_2027=<token>
MOODLE_DEFAULT_YEAR=2026
```

Each academic year is a separate Moodle site (`<base>/<year>`) with its own token.
Add a `MOODLE_TOKEN_<year>` line per year; no code changes needed.

### Getting a token (SSO login)

1. Log in to `https://moodle.runi.ac.il/<year>` in your browser.
2. Open DevTools (F12) → Network → enable *Preserve log*.
3. Visit:
   `https://moodle.runi.ac.il/<year>/admin/tool/mobile/launch.php?service=moodle_mobile_app&passport=12345&urlscheme=moodlemobile`
4. The page redirects to `moodlemobile://token=<base64>`. Base64-decode it; the result is
   `<signature>:::<token>`. Use the part after `:::`.

Treat the token like a password. To revoke it, log out of the Moodle app or remove it under
*Preferences → Security keys*.

## Connect to Claude Code

```
claude mcp add moodle -- uv run --directory <path-to-this-repo> moodle-mcp
```

## Project layout

```
src/moodle_mcp/
  config.py       # reads .env, resolves site URL + token per year
  client.py       # calls the Moodle REST API
  assignments.py  # assignment listing + new-assignment detection
  server.py       # FastMCP tool definitions
docs/
  moodle_functions.md  # API functions available to the token
```
