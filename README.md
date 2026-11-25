# Moodle MCP

Lets your AI (Claude, ChatGPT, ...) read your Reichman University Moodle and Yedion.

> [!WARNING]
> Never share your connector URL or your keys.

## Setup (about 15 minutes)

1. Get your Moodle key: [docs/moodle-key.md](docs/moodle-key.md)
2. [Fork this repo](https://github.com/shanikn/Moodle_MCP/fork).
3. Deploy it to Google Cloud Run: [docs/cloud-run.md](docs/cloud-run.md)
4. Copy your connector URL: `https://<your-host>/<your-secret>/mcp`
5. Add it as a custom connector in your AI app: [docs/connect-ai.md](docs/connect-ai.md)

## What you can ask

- *"What's due this week?"*
- *"Did the lecturer post anything new in Data Structures?"*
- *"When and where are my exams?"*
- *"Summarize this week's lecture slides."*

## Cost

Free for normal use. Google needs a credit card on file: [docs/cost.md](docs/cost.md)

## Stuck?

[Open an issue](https://github.com/shanikn/Moodle_MCP/issues) or message me ([shanikn](https://github.com/shanikn)).

---

More: [run it on your own computer](docs/local-setup.md) ·
[advanced notes](docs/advanced.md) · [technical details](docs/technical.md) ·
[MIT License](LICENSE)
