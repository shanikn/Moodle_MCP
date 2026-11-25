# Add it to your AI app

You need your connector URL from [cloud-run.md](cloud-run.md#check-it):
`https://<your-host>/<your-secret>/mcp`. Some apps need a paid plan for custom connectors.
[Back to setup](../README.md#setup-about-15-minutes)

## Claude (tested)

1. On [claude.ai](https://claude.ai), open **Settings → Connectors**.
2. Click **Add custom connector**.
3. Name it `Moodle` and paste your connector URL.
4. Click **Add**, then **Connect** (the sign-in page approves itself).
5. In a new chat, ask *"What's due this week on Moodle?"*

It also works in the Claude phone app with the same account.

## ChatGPT (not tested yet - tell me if it works)

Needs a paid ChatGPT plan.

1. Go to [chatgpt.com/plugins](https://chatgpt.com/plugins) and click **Add**.
2. Choose to create a custom MCP server.
3. Paste your connector URL.

## Other apps

- Apps on the web or phone (remote connectors): use the same connector URL.
- Apps on your computer (local MCP servers): follow [local-setup.md](local-setup.md) and use the
  same `"command"` / `"args"` as its Claude Desktop config.
