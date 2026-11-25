# HomeAPI — weekly meal-planner

FastAPI + SQLite backend and a single-page vanilla-JS frontend for planning lunches and dinners,
storing recipes (ingredients + steps), and pushing a recipe's shopping list to
[Bring!](https://www.getbring.com/).

The code, the API field names and the UI strings are **Spanish** (`nombre`, `comida`, `dia`, `mes`,
`año`). Documentation, comments and commit messages are written in **English**. Keep both
conventions as they are — do not rename Spanish identifiers.

## Layout

| Path | What it is |
|---|---|
| `app/main.py` | FastAPI app, API-key middleware, CORS, router registration |
| `app/db.py` | SQLite connection factory + `init_database()` (schema as `CREATE TABLE IF NOT EXISTS`) |
| `app/schemas.py` | All Pydantic models (in/out/update) — one file, no per-domain split |
| `app/crud.py` | Every DB operation, plain `sqlite3` with raw SQL. Routers hold no SQL |
| `app/calendar_config.py` | Google Calendar settings read from env, slot definitions and times |
| `app/calendar_sync.py` | Outbox worker that publishes `daily_menu` rows as calendar events |
| `app/routers/` | `categories.py`, `meals.py`, `ingredients.py`, `daily_menu.py`, `bring.py`, `calendar.py` |
| `index.html` | The whole UI markup (`index_backup.html` is a stale copy, ignore it) |
| `assets/js/app.js` | One `MenuApp` class, ~1700 lines, all app logic and rendering |
| `assets/css/styles.css` | All styles |
| `data/home_menu.db` | The SQLite file — **committed to the repo**, contains real data |
| `test_api.py` | Import/DB smoke script, not pytest. **Two of its four checks fail on `main`** — it calls `crear_comida` with the old signature, and `httpx2` is missing |
| `test_calendar_sync.py` | Calendar sync tests with Google faked out — no network, no credentials |
| `scripts/` | Throwaway Bring! exploration scripts |

Docs are numerous and partly stale: `INDEX.md` is the entry point; `README.md` documents endpoints
under `/menu` but the router actually mounts them at `/daily-menu`, and `meals` no longer has a
`descripcion` field. Trust the code over the `.md` files, and prefer fixing a doc you notice is wrong.

## Architecture rules that already hold

- **Layering is strict**: router → `crud` → sqlite. A router validates and maps errors
  (`ValueError` → HTTP 400, `None` → HTTP 404); it never opens a connection.
- **Every `crud` function opens its own connection** via the `get_conn()` context manager and commits
  itself. There is no shared session or transaction spanning calls.
- **Schema migrations do not exist.** `init_database()` only creates missing tables; it never
  `ALTER`s. Adding a column to an existing table means writing the `ALTER TABLE` guard yourself
  (check `PRAGMA table_info` first) — otherwise existing `data/home_menu.db` installs silently keep
  the old shape and every query against the new column fails at runtime.
- **`daily_menu` is one row per day**, keyed `UNIQUE(mes, año, dia)`, with two nullable FKs:
  `meal_lunch_id` and `meal_dinner_id`. There is no `date` column — the date is three integers.
- `PUT /daily-menu/{id}` **always writes both** meal ids, so omitting one in the payload clears it.
  That is deliberate (it is how the UI removes a meal), so don't "fix" it into a partial update.
- Meal edits **replace** their children: `actualizar_comida` deletes and reinserts all
  `meal_ingredients` and `meal_steps` when those keys are present. Steps are renumbered 1..n by
  `_replace_meal_steps`; `step_order` is not a stable id.
- Ingredient `spec` is free text ("200 g", "2"). `_merge_specs` in `crud.py` concatenates with `/`;
  `_merge_bring_specs` in `routers/bring.py` tries to *sum* quantities with matching units instead.
  They are intentionally different — don't unify them.

## Google Calendar sync

Each day publishes up to two events (lunch 14:00, dinner 21:00) to a **secondary** calendar shared
with a service account. One-way only: the DB is the source of truth and edits made in Google are
overwritten on the next sync of that slot.

It follows the **outbox pattern**. A `crud` mutation writes the affected `(mes, año, dia, slot)` into
`calendar_sync_queue` inside its own transaction and commits; a background thread started on FastAPI
startup drains the queue with exponential backoff (6 attempts, then the entry is dropped and logged).
So a Google outage never fails a `PUT`, and pending work survives a container restart.

- **Queue entries say "this slot is dirty", never which operation to perform.** The worker rereads
  the current state and decides create/update/delete. That is what makes retries idempotent — keep
  it that way when adding triggers.
- **Any mutation that changes event content must enqueue the affected slots**, and the slot list must
  be read *before* a delete. `eliminar_comida` and `eliminar_ingrediente` do this because their
  cascades (`ON DELETE SET NULL`, `ON DELETE CASCADE`) erase the link the query needs. Forget it and
  the events are orphaned in the calendar with no record of them.
- `calendar_events` is keyed by `(mes, año, dia, slot)`, not by `daily_menu_id`, so deleting and
  recreating a day still finds its event.
- `content_hash` skips the Google call when nothing actually changed; a full month re-sync of
  unchanged days costs zero API calls.
- A `404`/`410` from Google on update means someone deleted the event by hand: the code drops the
  local mapping and recreates it rather than failing forever.
- `daily_menu` accepts `dia` up to 31 for any month, so 31/02 is storable. `slot_window` returns
  `None` for such dates and the slot publishes nothing.
- The integration is **inert unless `GOOGLE_CALENDAR_ENABLED=1` and `GOOGLE_CALENDAR_ID` are both
  set** — `_enqueue_slots` returns immediately, so nothing accumulates when it is off.
- `POST /calendar/sync?mes=&año=` reconciles a whole month (initial backfill, or fixing divergence);
  `GET /calendar/status` reports pending work and recent failures.

## Configuration

Environment variables, read at import time:

- `DB_PATH` — SQLite file. Defaults to `<repo>/data/home_menu.db`; Docker sets `/data/home_menu.db`.
- `API_KEY` — value expected in the `X-API-Key` header. Default `homeapi_default_key_2024`.
- `DISABLE_API_KEY_AUTH` — `1`/`true`/`yes` turns auth off entirely. `run-api.ps1` sets it so the
  `file://` frontend works locally.
- `BRING_EMAIL` / `BRING_PASSWORD` — fallback Bring! credentials when the request body omits them.
- `GOOGLE_CALENDAR_ENABLED` — `1`/`true`/`yes` activates the calendar sync. Off by default.
- `GOOGLE_CALENDAR_ID` — the secondary calendar's id. Required; without it the sync stays off.
- `GOOGLE_SERVICE_ACCOUNT_FILE` — service-account JSON. Default `/secrets/google-service-account.json`.
- `CALENDAR_TIMEZONE` — default `Europe/Madrid`.
- `CALENDAR_LUNCH_TIME` / `CALENDAR_DINNER_TIME` — `HH:MM`, default `14:00` and `21:00`.
- `CALENDAR_LUNCH_DURATION_MINUTES` / `CALENDAR_DINNER_DURATION_MINUTES` — default 60.
- `CALENDAR_WORKER_POLL_SECONDS` — worker poll interval, default 20, floor 5.

Public paths that skip auth: `/`, `/docs`, `/redoc`, `/openapi.json`. `OPTIONS` always passes.

The API key is hardcoded in `assets/js/app.js` alongside the base URL: `localhost:8000` when served
from `file://` or localhost, `https://homeapi.beadpaws.es` otherwise. Bring's list UUID is hardcoded
too (`FIXED_BRING_LIST_UUID` in `routers/bring.py`); the `list_uuid` request field is accepted and
then ignored.

## Running it

```powershell
.\run-api.ps1                  # venv + deps + uvicorn on :8000, auth disabled
.\run-complete.ps1             # the above plus python -m http.server 3000 and opens the browser
python test_calendar_sync.py   # calendar sync tests, Google faked out
python test_api.py             # import + database smoke check (2 checks fail on main already)
docker compose up -d           # container on :8000, DB bind-mounted from ./data
```

There is no pytest suite, no linter config and no CI. Run `test_calendar_sync.py` after touching
`crud.py`, `calendar_sync.py` or `calendar_config.py` — it needs no credentials and never calls
Google, and it is where the regression net for the sync triggers lives. Add a case there for any new
mutation that should propagate to the calendar.

## Working conventions

- Work happens on feature branches (`feature/<topic>`); PRs target `main`.
- **Don't commit or push unless asked.** Same for creating PRs.
- Careful with `data/home_menu.db`: it is tracked, so any local run that mutates data shows up as a
  binary diff. Don't stage it unless the change is intentional.
- `app/**/__pycache__/*.pyc` files are tracked in git (there is no `.gitignore`). Don't add more, and
  don't mass-delete them as a drive-by change either.
- New endpoints go in the matching router with its existing `prefix`/`tags` shape, with the SQL in
  `crud.py` and the models in `schemas.py`.
