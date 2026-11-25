# Google Calendar setup

HomeAPI can publish each day's lunch and dinner as events on a dedicated Google Calendar. This is a
one-way sync: the database is the source of truth, and any edit made directly in Google Calendar is
overwritten the next time that day changes.

The integration is off by default and stays completely inert until both `GOOGLE_CALENDAR_ENABLED=1`
and `GOOGLE_CALENDAR_ID` are set.

## 1. Create the secondary calendar

1. Open [Google Calendar](https://calendar.google.com) on the web.
2. In the left sidebar, next to **Other calendars**, click **+** → **Create new calendar**.
3. Name it (for example `Menú`), set the time zone to **Europe/Madrid**, and click
   **Create calendar**.
4. Open **Settings and sharing** for the new calendar and scroll to **Integrate calendar**.
5. Copy the **Calendar ID**. It looks like
   `c_a1b2c3d4e5f6@group.calendar.google.com`. Keep it — it is `GOOGLE_CALENDAR_ID`.

Keeping this separate from your main calendar means you can hide it, colour it independently, and a
bulk deletion can never touch your real appointments.

## 2. Create the service account

A service account is a robot Google account with its own credentials. It suits a backend with nobody
sitting in front of it: there is no consent screen and no refresh token that can expire.

1. Go to the [Google Cloud console](https://console.cloud.google.com) and create a project (or reuse
   one) — for example `homeapi`.
2. **APIs & Services** → **Library** → search **Google Calendar API** → **Enable**.
3. **APIs & Services** → **Credentials** → **Create credentials** → **Service account**.
   - Name: `homeapi-calendar`. No roles are needed: access comes from calendar sharing, not IAM.
4. Open the service account → **Keys** tab → **Add key** → **Create new key** → **JSON** → **Create**.
   A `.json` file downloads. This is the only copy — Google will not show it again.
5. Copy the service account's email from its **Details** tab. It looks like
   `homeapi-calendar@homeapi-123456.iam.gserviceaccount.com`.

## 3. Share the calendar with the service account

1. Back in Google Calendar, open the new calendar's **Settings and sharing**.
2. Under **Share with specific people or groups**, click **Add people and groups**.
3. Paste the service account email.
4. Set the permission to **Make changes to events**, then **Send**.

Without this step every API call fails with `404 Not Found`, because the service account simply
cannot see a calendar nobody shared with it.

## 4. Install the credentials

Put the downloaded JSON at `secrets/google-service-account.json` in the repo root:

```powershell
mkdir secrets
Move-Item "$env:USERPROFILE\Downloads\homeapi-123456-abcdef.json" secrets\google-service-account.json
```

`secrets/*.json` is gitignored. **Do not commit this file** — it grants write access to the calendar
to anyone who has it. If it ever leaks, delete the key in the Cloud console and create a new one.

## 5. Configure and start

With Docker, create a `.env` file next to `docker-compose.yml`:

```
GOOGLE_CALENDAR_ENABLED=1
GOOGLE_CALENDAR_ID=c_a1b2c3d4e5f6@group.calendar.google.com
```

Then:

```powershell
docker compose up -d --build
```

Locally, set the variables in the shell before starting uvicorn:

```powershell
$env:GOOGLE_CALENDAR_ENABLED = "1"
$env:GOOGLE_CALENDAR_ID = "c_a1b2c3d4e5f6@group.calendar.google.com"
$env:GOOGLE_SERVICE_ACCOUNT_FILE = "$PWD\secrets\google-service-account.json"
.\run-api.ps1
```

Note the local path: the default `/secrets/google-service-account.json` is the container's path.

## 6. Verify and backfill

Check the integration is live:

```powershell
curl -H "X-API-Key: homeapi_default_key_2024" http://localhost:8000/calendar/status
```

`enabled` should be `true` and `calendar_id` should show your calendar.

Existing days are not published automatically — only changes made from now on are. To publish a month
that already has a menu:

```powershell
curl -X POST -H "X-API-Key: homeapi_default_key_2024" `
  "http://localhost:8000/calendar/sync?mes=3&año=2026"
```

The response reports how many slots were queued and what happened to each. Run the same call any time
you suspect the calendar has drifted from the database: it is safe to repeat, and unchanged days cost
no API calls.

## How it behaves day to day

- Assigning or changing a meal updates that day's event within a few seconds.
- Clearing a meal from a day deletes its event. Deleting the day deletes both.
- Renaming a meal, or editing its ingredients or steps, updates **every** day that uses it.
- Deleting a meal removes it from every day that referenced it, and their events go too.
- The event title is `Comida: <meal>` or `Cena: <meal>`; the description carries the ingredients (with
  quantities), the numbered steps, and the categories.

## Settings reference

| Variable | Default | Meaning |
|---|---|---|
| `GOOGLE_CALENDAR_ENABLED` | `0` | `1`/`true`/`yes` activates the sync |
| `GOOGLE_CALENDAR_ID` | — | Calendar ID from step 1. Required |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | `/secrets/google-service-account.json` | Path to the JSON key |
| `CALENDAR_TIMEZONE` | `Europe/Madrid` | Time zone of the events |
| `CALENDAR_LUNCH_TIME` | `14:00` | Lunch start, `HH:MM` |
| `CALENDAR_DINNER_TIME` | `21:00` | Dinner start, `HH:MM` |
| `CALENDAR_LUNCH_DURATION_MINUTES` | `60` | Lunch length |
| `CALENDAR_DINNER_DURATION_MINUTES` | `60` | Dinner length |
| `CALENDAR_WORKER_POLL_SECONDS` | `20` | How often the worker checks for pending work |

## Troubleshooting

**Nothing appears in the calendar.** Check `GET /calendar/status`. If `enabled` is `false`, one of the
two required variables is missing. If `pending` keeps growing, look at `recent_failures` — it carries
the error Google returned.

**`404 Not Found` from Google.** Either the calendar ID is wrong, or step 3 was skipped and the
service account has no access.

**`403 Forbidden`.** The Calendar API is not enabled on the project (step 2.2), or the service account
was shared with read-only permission instead of *Make changes to events*.

**`Service account file not found`.** The path in `GOOGLE_SERVICE_ACCOUNT_FILE` does not exist inside
the process. In Docker, confirm the `./secrets:/secrets:ro` volume is mounted.

**A day is stuck failing.** After 6 attempts with exponential backoff the entry is dropped and the
error logged (`docker compose logs -f home-api`). Fix the cause, then re-run the month sync.
