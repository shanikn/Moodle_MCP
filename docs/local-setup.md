# Run it on your own computer

Instead of the cloud setup in the [README](../README.md), you can run the program on your own
computer. No credit card is needed, but it only works while your computer is on and the Claude
desktop app is open on it (not on claude.ai or the phone app). It needs an Israeli internet connection. About 15 minutes.

Before you start, get [your Moodle key](moodle-key.md) and
have [your settings](cloud-run.md#variables) ready. Leave out `MCP_TRANSPORT` and
`MCP_SECRET_PATH`: they are only for the cloud.

## Install

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

## Download the program

5. On the [project page](https://github.com/shanikn/Moodle_MCP), click the green **Code** button, then **Download ZIP**.
6. Unzip it into your **Documents** folder.
7. Rename the unzipped folder from `Moodle_MCP-main` to `Moodle_MCP`.

## Add your settings

8. In the `Moodle_MCP` folder, open `.env.example` with a text editor (Notepad on Windows,
   TextEdit on Mac).
   On a Mac, if you don't see the file, press Cmd+Shift+. (period) in Finder to show hidden files.
9. Fill in [your settings](cloud-run.md#variables) after each `=`, with no spaces or quotes.
10. Save it under the new name `.env` in the same folder.
    - **Windows (Notepad):** File → Save As, set *Save as type* to **All files**, and name it
      `.env`. Otherwise it becomes `.env.txt` and won't work.
    - **Mac (TextEdit):** first choose Format → **Make Plain Text**, then save as `.env`. If asked,
      choose **Use ".env"**.

## Check that it starts

11. In the terminal, go to the folder:
    - **Windows:** `cd $HOME\Documents\Moodle_MCP`
    - **Mac:** `cd ~/Documents/Moodle_MCP`
12. Run `uv run moodle-mcp`. The first time, it downloads what it needs (a minute or two).
13. If it then waits without showing an error, it works. Press **Ctrl+C** to stop it.
    If you see an error, check your `.env` file, especially the key and the year.

## Connect it to Claude

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

## A new academic year

Add the new `MOODLE_TOKEN_<year>` line to `.env`, change `MOODLE_DEFAULT_YEAR`, then quit and
reopen Claude. For the cloud version see [cloud-run.md](cloud-run.md#change-a-setting).

Keep your `.env` file private: never send it to anyone or upload it to GitHub.
