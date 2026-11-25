# Deploy to Google Cloud Run

You need your [Moodle key](moodle-key.md), your [fork](https://github.com/shanikn/Moodle_MCP/fork)
of this repo, and a Google account with a credit card ([why](cost.md)).
[Back to setup](../README.md#setup-about-15-minutes)

## Make your secret code

1. In Chrome, press **F12** and click the **Console** tab.
2. Paste this and press Enter:
   ```
   crypto.randomUUID().replaceAll("-", "") + crypto.randomUUID().replaceAll("-", "")
   ```
3. Save the result (without quotes) in your private note. This is your **secret code**.

## Set up Google Cloud

4. Sign in to the [Google Cloud console](https://console.cloud.google.com).
5. Project picker (top) → **New project** → name it `moodle-mcp` → **Create**.
6. Select `moodle-mcp` in the project picker.
7. Menu (☰) → **Billing** → link a billing account (add your card).
8. Set a $1 budget alert: [cost.md](cost.md#set-a-1-budget-alert).

## Create the service

9. Open [Cloud Run](https://console.cloud.google.com/run) → **Create service** (enable APIs if asked).
10. Choose **Continuously deploy from a repository** → **Set up with Cloud Build**.
11. Choose **GitHub**, sign in, and give Cloud Build access to your fork.
12. Select your fork `Moodle_MCP` → **Next**.
13. Branch `^main$`, build type **Dockerfile**, source `/Dockerfile` → **Save**.
14. Region: `me-west1 (Tel Aviv)`.
15. Authentication: **Allow public access**.
16. Scaling: minimum instances `0`, maximum instances `1`.
17. Open **Containers, Volumes, Networking, Security** → **Variables & Secrets**.
18. Add each variable from the [table below](#variables).
19. Click **Create** and wait for the green check (about 5 minutes).

## Check it

20. Copy the service **URL** at the top, e.g. `https://moodle-mcp-123456789.me-west1.run.app`.
21. Open `<URL>/<secret code>/due` in your browser: it should show what's due.
22. Your connector URL is `<URL>/<secret code>/mcp`.

Next: [add it to your AI app](connect-ai.md).

## Variables

| Name | Value |
|---|---|
| `MOODLE_BASE_URL` | `https://moodle.runi.ac.il` |
| `MOODLE_TOKEN_2027` | your Moodle key (change `2027` in the name to your year) |
| `MOODLE_DEFAULT_YEAR` | your year, e.g. `2027` |
| `RUNI_USERNAME` | your university username (optional) |
| `RUNI_PASSWORD` | your university password (optional) |
| `MCP_TRANSPORT` | `http` |
| `MCP_SECRET_PATH` | your secret code |

- Without `RUNI_USERNAME` / `RUNI_PASSWORD`, only the Yedion tools (exams, timetable, exam bank,
  exam notebooks) are off.
- Don't add `PORT`: Google sets it.
- The region must be in Israel: Moodle and Yedion block connections from abroad.
- Public access is needed so your AI app can reach it; the secret code keeps others out.
- Max 1 instance, because each instance logs in to Yedion separately.

## Getting updates

1. On your fork on GitHub, click **Sync fork** → **Update branch**.
2. Cloud Run rebuilds by itself within a few minutes.

## Change a setting

1. For a new year, get a new key with [moodle-key.md](moodle-key.md).
2. Cloud Run → your service → **Edit & deploy new revision**.
3. Under **Variables & Secrets**, add `MOODLE_TOKEN_<new year>` (keep the old one to read last year).
4. Change `MOODLE_DEFAULT_YEAR` to the new year.
5. Click **Deploy**.
