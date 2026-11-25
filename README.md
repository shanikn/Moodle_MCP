# Moodle MCP

Lets your AI assistant read your Reichman University Moodle and Yedion, so you can ask things like:

- *"What's due this week?"*
- *"Did the lecturer post anything new in Data Structures?"*
- *"When and where are my exams?"*
- *"Summarize this week's lecture slides."*
- *"Find past exams for Linear Algebra."*

> **For Reichman University (RUNI) students only.** It uses RUNI's Moodle
> (`moodle.runi.ac.il`) and My RUNI / Yedion, and logs in with your own student account.
> It only reads. It never submits, changes or deletes anything.

Works with any AI app that supports MCP connectors (for example Claude, ChatGPT or Cursor).
The steps below use Claude, the tested example; for other apps see [Other AI apps](#other-ai-apps).

> [!WARNING]
> **Never share your connector URL or your `.env` file, and never upload `.env` to GitHub.** Anyone who has either one can read your Moodle, grades and exams.

## Before you start

You need:

- A Reichman student account (the one you use for Moodle and My RUNI).
- An Israeli internet connection. Moodle and Yedion block connections from abroad.
- An AI app that supports MCP connectors. The steps use [Claude](https://claude.ai). Some apps
  need a paid plan to add your own (custom) connectors.

Then pick one option:

| | **A) On your own computer** | **B) In the cloud** |
|---|---|---|
| Works | only while your computer is on and the Claude app is open on it | anytime, also on claude.ai and the Claude phone app |
| Needs | the Claude desktop app | a GitHub account and a Google Cloud account |
| Credit card | not needed | needed: Google requires one for billing, but normal use stays free |
| Time | about 15 minutes | about 30 minutes |

**Does it cost money?** Option A is completely free. Option B is free for normal personal use:
it stays well within Google Cloud's monthly free tier (2 million requests plus free CPU and memory time), but Google still requires a credit card for billing.
The only possible small cost: each deploy stores a copy of the program (a *container image*) in Artifact Registry, and old copies can go past the free storage.
To prevent that, after your first deploy open [Artifact Registry](https://console.cloud.google.com/artifacts) → the `cloud-run-source-deploy` repository (region `me-west1`) → **Edit** → **Cleanup policies**: add a **Delete artifacts** policy (tag state *Any*), then a **Keep most recent versions** policy with count `3`, and click **Update**.
Also set the $1 budget alert (Option B, steps 10–13).

Both options start with **Step 1: get your Moodle key**.

## Step 1: get your Moodle key

The Moodle key (called a *token*) lets the program read Moodle as you. Do this on a computer,
in Chrome or Edge. You only need to do it once per academic year.

1. Log in to Moodle at `https://moodle.runi.ac.il/2027`.
   The number at the end is the academic year. Use the number you see in your own Moodle address.
2. Open the developer panel: press **F12** (or **Ctrl+Shift+I**; on a Mac **Cmd+Option+I**).
   A panel opens at the side or bottom of the window.
3. At the top of that panel, click the **Network** tab. If you don't see it, click **»** and
   choose **Network**.
4. Just below the tabs, tick the **Preserve log** checkbox.
5. Click the browser's address bar (still the same tab), paste this link, change `2027` to your
   year, and press Enter:
   ```
   https://moodle.runi.ac.il/2027/admin/tool/mobile/launch.php?service=moodle_mobile_app&passport=12345&urlscheme=moodlemobile
   ```
   The page may stay blank or show an error. That's normal. If the browser asks whether to open
   an app, click **Cancel**.
6. In the panel's **Filter** box (top left of the Network tab), type `launch`.
7. Click the line that starts with `launch.php?service=moodle_mobile_app`. Its status is `303`.
8. On the right, the **Headers** tab opens. Scroll down to **Response Headers** and find
   **location**. Its value looks like this (yours is longer):
   ```
   moodlemobile://token=YWJjMTIzOjo6ZXhhbXBsZTo6Onh5ejc4OQ==
   ```
9. Select the whole value, from `moodlemobile` to the end, and press **Ctrl+C** (Mac: **Cmd+C**).
10. In the panel, click the **Console** tab.
11. Paste this line, then replace `PASTE_HERE` with what you copied (keep the quotes):
    ```
    atob("PASTE_HERE".split("token=").pop()).split(":::")[1]
    ```
    Press Enter. If the browser first asks you to type `allow pasting`, type it, press Enter,
    and paste the line again.
12. The console prints your Moodle key in quotes, e.g. `"0123456789abcdef0123456789abcdef"`
    (32 letters and numbers). Copy it without the quotes.
13. Save the key in a private note. Treat it like a password.

Stuck in this step? Message me ([shanikn](https://github.com/shanikn)) and we'll find another way.

### Your settings

Both options use the same settings:

| Setting | What to write |
|---|---|
| `MOODLE_BASE_URL` | `https://moodle.runi.ac.il` (leave as is) |
| `MOODLE_TOKEN_2027` | your Moodle key. Change `2027` in the name to your year |
| `MOODLE_DEFAULT_YEAR` | your year, e.g. `2027` |
| `RUNI_USERNAME` | your university username (optional, for exams, timetable and exam bank) |
| `RUNI_PASSWORD` | your university password (optional, same) |

Without `RUNI_USERNAME` and `RUNI_PASSWORD`, everything that comes from Moodle still works.
Only the exam schedule, class timetable, exam bank and graded exam notebooks (from Yedion) need them.

## Option A: run it on your own computer

### Install

1. Download and install the [Claude desktop app](https://claude.ai/download), then log in.
2. Open a terminal (a window where you type commands):
   - **Windows:** press Start, type `PowerShell`, and open **Windows PowerShell**.
   - **Mac:** press Cmd+Space, type `Terminal`, and press Enter.
3. Install **uv**, the tool that runs this program (it also installs Python for you). Paste the
   line for your system into the terminal and press Enter:
   - **Windows:**
     ```
     powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
   - **Mac:**
     ```
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
4. Close the terminal window. Open a new one so it finds uv.

### Download the program

5. On this page on GitHub, click the green **Code** button, then **Download ZIP**.
6. Unzip it into your **Documents** folder.
7. Rename the unzipped folder from `Moodle_MCP-main` to `Moodle_MCP`.

### Add your settings

8. In the `Moodle_MCP` folder, open `.env.example` with a text editor (Notepad on Windows,
   TextEdit on Mac).
   On a Mac, if you don't see the file, press Cmd+Shift+. (period) in Finder to show hidden files.
9. Fill in [your settings](#your-settings) after each `=`, with no spaces or quotes.
10. Save it under the new name `.env` in the same folder.
    - **Windows (Notepad):** File → Save As, set *Save as type* to **All files**, and name it
      `.env`. Otherwise it becomes `.env.txt` and won't work.
    - **Mac (TextEdit):** first choose Format → **Make Plain Text**, then save as `.env`. If asked,
      choose **Use ".env"**.

### Check that it starts

11. In the terminal, go to the folder:
    - **Windows:** `cd $HOME\Documents\Moodle_MCP`
    - **Mac:** `cd ~/Documents/Moodle_MCP`
12. Run `uv run moodle-mcp`. The first time, it downloads what it needs (a minute or two).
13. If it then waits without showing an error, it works. Press **Ctrl+C** to stop it.
    If you see an error, check your `.env` file, especially the key and the year.

### Connect it to Claude

14. In the Claude desktop app, open **Settings → Developer → Edit Config**. This opens a file
    called `claude_desktop_config.json`.
15. Replace its content with the text below. Change `<you>` to your user name on the computer
    (the name in the path of your Documents folder):
    - **Windows:**
      ```json
      {
        "mcpServers": {
          "moodle": {
            "command": "uv",
            "args": ["run", "--directory", "C:/Users/<you>/Documents/Moodle_MCP", "moodle-mcp"]
          }
        }
      }
      ```
    - **Mac:**
      ```json
      {
        "mcpServers": {
          "moodle": {
            "command": "uv",
            "args": ["run", "--directory", "/Users/<you>/Documents/Moodle_MCP", "moodle-mcp"]
          }
        }
      }
      ```
    If the file already had other entries under `mcpServers`, add the `"moodle"` block next to
    them instead of replacing everything.
16. Save the file.
17. Quit Claude completely and open it again. On Windows, right-click the Claude icon near the
    clock and choose **Quit**. On a Mac, press Cmd+Q.
18. In a new chat, ask *"What's due this week on Moodle?"*

If Claude says it can't start the `moodle` server, the app can't find uv. In the terminal, run
`where.exe uv` (Windows) or `which uv` (Mac), and put the path it prints in place of `"uv"` after
`"command"` (on Windows, write it with `/` instead of `\`).

Using Claude Code instead? Run
`claude mcp add moodle -- uv run --directory <path-to-Moodle_MCP> moodle-mcp`.

## Option B: run it in the cloud

The program runs on Google Cloud Run, in Google's Tel Aviv data center, and you add it to
claude.ai as a *connector*. It only runs while Claude is using it, so normal use stays inside
Google's free allowance.

### Make your own copy of the code

1. Sign in to [GitHub](https://github.com) (create a free account if you don't have one).
2. Open [this project's page](https://github.com/shanikn/Moodle_MCP) and click **Fork**, then
   **Create fork**. This makes your own copy. It contains no passwords: you add those in Google
   Cloud only.

### Make your secret link code

Your connector link includes a secret code that only you know. It works like a password.

3. In Chrome, press **F12** and open the **Console** tab.
4. Paste this and press Enter:
   ```
   crypto.randomUUID().replaceAll("-", "") + crypto.randomUUID().replaceAll("-", "")
   ```
5. Copy the result (64 letters and numbers, without the quotes) and save it in your private note.
   This is your **secret code**.

### Set up Google Cloud

6. Go to the [Google Cloud console](https://console.cloud.google.com) and sign in with your
   Google account. Accept the terms if asked.
7. Click the project picker at the top, then **New project**. Name it `moodle-mcp` and click
   **Create**.
8. Make sure `moodle-mcp` is selected in the project picker at the top.
9. Open the menu (☰), then **Billing**, and link a billing account. To create one, add your
   credit card. Google requires this even when you stay free.
10. In **Billing**, open **Budgets & alerts**, then click **Create budget**.
11. Name it `moodle`, choose your `moodle-mcp` project, and click **Next**.
12. Set the amount to **$1** and click **Next**.
13. Keep the email alerts at 50%, 90% and 100%, and click **Finish**.

### Create the service

14. Open [Cloud Run](https://console.cloud.google.com/run) and click **Create service** (it may
    say **Deploy container**, then **Service**). If asked to enable an API, click **Enable**.
15. Choose **Continuously deploy from a repository**, then click **Set up with Cloud Build**.
16. Choose **GitHub**, sign in, and allow Google Cloud Build to access your fork (you can choose
    only that repository).
17. Select your fork `Moodle_MCP` and click **Next**.
18. Set the branch to `^main$`, the build type to **Dockerfile**, and the source location to
    `/Dockerfile`. Click **Save**.
19. Set **Region** to `me-west1 (Tel Aviv)`. It must be in Israel, because Moodle and Yedion
    block connections from abroad.
20. Under **Authentication**, choose **Allow public access**. claude.ai has to be able to reach
    it. Your secret code is what keeps others out.
21. Under scaling, set **Minimum number of instances** to `0` (so it costs nothing when unused)
    and **Maximum number of instances** to `1`.
22. Open **Containers, Volumes, Networking, Security**, then the **Variables & Secrets** tab.
23. Click **Add variable** for each of [your settings](#your-settings) (name on the left, value on
    the right), and add these two more:

    | Name | Value |
    |---|---|
    | `MCP_TRANSPORT` | `http` |
    | `MCP_SECRET_PATH` | your secret code |

    Don't add `PORT`. Google sets it.
24. Click **Create**. Wait until the service shows a green check mark (about 5 minutes the first
    time).

### Check it

25. Copy the service **URL** at the top of the page. It looks like
    `https://moodle-mcp-123456789.me-west1.run.app`.
26. In your browser, open your URL followed by `/` + your secret code + `/due`, for example
    `https://moodle-mcp-123456789.me-west1.run.app/<secret code>/due`.
    You should see what's due soon. If you see *Not Found*, check the secret code in the link.

### Add it to Claude

27. On [claude.ai](https://claude.ai), open **Settings → Connectors**.
28. Click **Add custom connector**.
29. Name it `Moodle`. As the URL, enter your service URL followed by `/` + your secret code +
    `/mcp`, for example `https://moodle-mcp-123456789.me-west1.run.app/<secret code>/mcp`.
30. Click **Add**, then **Connect**. The sign-in page approves itself.
31. In a new chat, ask *"What's due this week on Moodle?"* The connector also appears in the
    Claude phone app when you log in with the same account.

### Getting updates

When this project gets new features, open your fork on GitHub and click **Sync fork**, then
**Update branch**. Google Cloud rebuilds your service by itself within a few minutes.

To change a setting later (for example a new year's key), open your service in Cloud Run, click
**Edit & deploy new revision**, change the variable under **Variables & Secrets**, and click
**Deploy**.

## Other AI apps

This is a standard MCP server, so other apps that support MCP can use it too:

- **Apps on the web or phone (remote connectors):** use the same connector URL as in Option B,
  `https://<your service URL>/<secret code>/mcp`.
- **Apps on your computer (local MCP servers):** run the same command as in the Claude Desktop
  config in Option A: `uv run --directory <path-to-Moodle_MCP> moodle-mcp`. Most apps accept the
  same `"command"` / `"args"` JSON.

**Example: ChatGPT** (not tested yet - tell me if it works). Needs a paid ChatGPT plan.

1. Do Option B first.
2. Go to [chatgpt.com/plugins](https://chatgpt.com/plugins) and click **Add**.
3. Choose to create a custom MCP server.
4. Enter the connector URL `https://<your service URL>/<secret code>/mcp`.

## A new academic year

Each academic year is a separate Moodle site with its own key. When the new year starts:

1. Do [Step 1](#step-1-get-your-moodle-key) again with the new year's number.
2. Add a new setting `MOODLE_TOKEN_<new year>` with the new key. You can keep the old one to
   still read last year's courses.
3. Change `MOODLE_DEFAULT_YEAR` to the new year.
4. Restart Claude (option A) or deploy a new revision (option B).

## Advanced / good to know

### The budget alert doesn't stop spending

The $1 budget only sends you emails. It doesn't switch anything off. If you ever get one, open
the project in Google Cloud and check what is running.

### Store your key and password in Secret Manager

In option B, instead of typing `MOODLE_TOKEN_<year>` and `RUNI_PASSWORD` as plain variables, you
can save them in Google Cloud **Secret Manager** and, under **Variables & Secrets**, choose
**Reference a secret**. Then they aren't shown in the service settings.

### "New assignments" in the cloud

Claude's *new assignments* answer works by remembering which assignments it has already seen.
On your computer that list stays saved. In the cloud it is forgotten whenever Google restarts
the service, so after a restart the first answer only starts a new list.

### If something leaks

If someone else might have your `.env` file, Moodle key, password or connector link:

1. In Moodle, open your profile menu → **Preferences** → **Security keys** and reset the
   *Moodle mobile web service* key. Then get a new key with [Step 1](#step-1-get-your-moodle-key).
2. Change your university password.
3. Option B: make a new secret code, update `MCP_SECRET_PATH` in Cloud Run, and update the
   connector link in claude.ai.

## Technical details

Full list of tools, how the Yedion login works, the iPhone Shortcut endpoint, tests and project
layout: [docs/technical.md](docs/technical.md). Every Moodle function a student key can use:
[docs/moodle_functions.md](docs/moodle_functions.md).

Licensed under the [MIT License](LICENSE).

## Stuck?

[Open a GitHub issue](https://github.com/shanikn/Moodle_MCP/issues) or message me
([shanikn](https://github.com/shanikn)). Never include your key, password or connector link.
