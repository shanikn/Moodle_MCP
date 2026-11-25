# Advanced / good to know

[Back to the README](../README.md)

Prefer running it on your own computer? See [local-setup.md](local-setup.md).

## If something leaks

If someone else might have your `.env` file, Moodle key, password or connector URL:

1. Moodle → profile menu → **Preferences → Security keys** → reset the *Moodle mobile web service* key.
2. Get a new key with [moodle-key.md](moodle-key.md).
3. Change your university password.
4. Make a new secret code ([cloud-run.md](cloud-run.md#make-your-secret-code)).
5. Update the variables in Cloud Run ([how](cloud-run.md#change-a-setting)).
6. Update the connector URL in your AI app.

## Store your key and password in Secret Manager

1. Save `MOODLE_TOKEN_<year>` and `RUNI_PASSWORD` in Google Cloud **Secret Manager**.
2. In Cloud Run, under **Variables & Secrets**, choose **Reference a secret** instead of a plain value.

Then they aren't shown in the service settings.

## "New assignments" in the cloud

The *new assignments* tool remembers which assignments it has already seen. On your computer
that list is saved; in the cloud it is forgotten whenever Google restarts the service, so the
first answer after a restart only starts a new list.

## Budget alerts don't stop spending

The $1 budget ([cost.md](cost.md)) only emails you. If you get one, check what is running.
