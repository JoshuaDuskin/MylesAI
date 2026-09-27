MYLES v8.2 — ONE FOLDER + FREE PHONE APP

GOAL
----
One visible Myles folder on the Desktop. No Twilio. No Telegram. No browser window on the tower.

SETUP
-----
Run the one-file setup normally (not Administrator). v8.2 creates its own Python environment under %LOCALAPPDATA%\MylesAI\.venv so it no longer depends on Desktop\DuskinAI. After the new core is verified healthy, the delayed cleanup moves the legacy DuskinAI and AutoLogon folders into Desktop\Myles\Legacy instead of deleting them.

PHONE
-----
Open Desktop\Myles\Enable Phone App.cmd once. It uses Tailscale to share the local Myles interface privately to your own iPhone. Tailscale Personal is free for personal use. Install Tailscale on the tower and iPhone, sign into the same personal account, then the helper enables Tailscale Serve and writes PHONE ACCESS.txt with your Myles URL. Open the URL once in Safari and choose Share > Add to Home Screen. After that Myles opens like an app.

No paid SMS provider is required. A Windows-only computer cannot reliably send free messages directly through Apple's iMessage network without an Apple-device bridge.
