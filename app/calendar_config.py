"""Google Calendar integration settings, read from environment variables."""

import os
from datetime import date, datetime, time, timedelta
from typing import Optional, Tuple

SLOT_LUNCH = 'lunch'
SLOT_DINNER = 'dinner'
SLOTS = (SLOT_LUNCH, SLOT_DINNER)

SLOT_MEAL_COLUMN = {
    SLOT_LUNCH: 'meal_lunch_id',
    SLOT_DINNER: 'meal_dinner_id',
}

SLOT_LABEL = {
    SLOT_LUNCH: 'Comida',
    SLOT_DINNER: 'Cena',
}


def _env_flag(name: str, default: str = '0') -> bool:
    return os.getenv(name, default).strip().lower() in {'1', 'true', 'yes'}


def _env_time(name: str, default: str) -> time:
    raw = os.getenv(name, default).strip()
    try:
        hour_text, _, minute_text = raw.partition(':')
        return time(int(hour_text), int(minute_text or 0))
    except (TypeError, ValueError):
        hour_text, _, minute_text = default.partition(':')
        return time(int(hour_text), int(minute_text or 0))


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def is_enabled() -> bool:
    """The integration stays fully inert unless enabled and configured."""
    return _env_flag('GOOGLE_CALENDAR_ENABLED') and bool(calendar_id())


def calendar_id() -> str:
    return os.getenv('GOOGLE_CALENDAR_ID', '').strip()


def credentials_file() -> str:
    return os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', '/secrets/google-service-account.json').strip()


def timezone_name() -> str:
    return os.getenv('CALENDAR_TIMEZONE', 'Europe/Madrid').strip() or 'Europe/Madrid'


def worker_poll_seconds() -> int:
    return max(5, _env_int('CALENDAR_WORKER_POLL_SECONDS', 20))


def slot_times(slot: str) -> Tuple[time, int]:
    """Start time and duration in minutes for a slot."""
    if slot == SLOT_LUNCH:
        return _env_time('CALENDAR_LUNCH_TIME', '14:00'), _env_int('CALENDAR_LUNCH_DURATION_MINUTES', 60)
    return _env_time('CALENDAR_DINNER_TIME', '21:00'), _env_int('CALENDAR_DINNER_DURATION_MINUTES', 60)


def slot_window(mes: int, año: int, dia: int, slot: str) -> Optional[Tuple[datetime, datetime]]:
    """Start/end datetimes for a slot, or None when the date does not exist.

    daily_menu allows dia up to 31 regardless of the month, so 31/02 can be
    stored. Such a row simply has no calendar event.
    """
    try:
        day = date(año, mes, dia)
    except ValueError:
        return None

    start_time, duration_minutes = slot_times(slot)
    start = datetime.combine(day, start_time)
    return start, start + timedelta(minutes=max(1, duration_minutes))
