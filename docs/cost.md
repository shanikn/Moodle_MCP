# Cost

Free for normal personal use. It stays well within Google Cloud's monthly free tier (2 million
requests plus free CPU and memory time). Google still requires a credit card for billing.
[Back to setup](../README.md#setup-about-15-minutes)

The only possible small cost: each deploy stores a copy of the program (a *container image*) in
Artifact Registry, and old copies can go past the free storage. Do both steps below.

## Set a $1 budget alert

1. In the [Google Cloud console](https://console.cloud.google.com), open **Billing → Budgets & alerts**.
2. Click **Create budget**.
3. Name it `moodle`, choose your `moodle-mcp` project → **Next**.
4. Amount: **$1** → **Next**.
5. Keep the email alerts at 50%, 90%, 100% → **Finish**.

The alert only emails you; it doesn't stop anything. If you get one, check what is running.

## Keep only the latest images (after your first deploy)

1. Open [Artifact Registry](https://console.cloud.google.com/artifacts).
2. Click the `cloud-run-source-deploy` repository (region `me-west1`).
3. Click **Edit**, then go to **Cleanup policies**.
4. Add a **Delete artifacts** policy with tag state *Any*.
5. Add a **Keep most recent versions** policy with count `3`.
6. Click **Update**.

A keep policy alone deletes nothing, so you need both.
