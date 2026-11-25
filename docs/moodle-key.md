# Get your Moodle key

The key (a *token*) lets the program read Moodle as you. Use Chrome or Edge on a computer in
Israel. Do this once per academic year. [Back to setup](../README.md#setup-about-15-minutes)

1. Log in to `https://moodle.runi.ac.il/2027` (use the year number from your own Moodle address).
2. Press **F12** (Mac: **Cmd+Option+I**) to open the developer panel.
3. Click the **Network** tab (if hidden, click **»**).
4. Tick **Preserve log**.
5. In the address bar, open this link (change `2027` to your year):
   ```
   https://moodle.runi.ac.il/2027/admin/tool/mobile/launch.php?service=moodle_mobile_app&passport=12345&urlscheme=moodlemobile
   ```
6. If the page stays blank or the browser offers to open an app, that's fine: click **Cancel**.
7. In the panel's **Filter** box, type `launch`.
8. Click the `launch.php?service=moodle_mobile_app` line (status `303`).
9. Under **Headers → Response Headers**, find **location**. It looks like this, but longer:
   ```
   moodlemobile://token=YWJjMTIzOjo6ZXhhbXBsZTo6Onh5ejc4OQ==
   ```
10. Select the whole value and copy it (**Ctrl+C**, Mac: **Cmd+C**).
11. Click the **Console** tab.
12. Paste this line, replace `PASTE_HERE` with what you copied (keep the quotes), press Enter:
    ```
    atob("PASTE_HERE".split("token=").pop()).split(":::")[1]
    ```
13. If the browser asks you to type `allow pasting`, type it, press Enter, and repeat step 12.
14. Copy the printed key (32 letters and numbers) without the quotes.
15. Save it in a private note. Treat it like a password.

Stuck? Message me ([shanikn](https://github.com/shanikn)) and we'll find another way.

Next: [deploy to Google Cloud Run](cloud-run.md).
