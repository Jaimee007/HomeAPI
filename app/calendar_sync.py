"""Publishes daily_menu rows as Google Calendar events.

The queue in calendar_sync_queue only records which (date, slot) pairs are
dirty. This module reads the current state of each dirty slot and decides
whether to create, update or delete its event, which makes every retry
idempotent: replaying a slot converges on the same result.
"""

import hashlib
import json
import logging
import os
import threading
import time as time_module
from typing import Any, Dict, List, Optional, Tuple

from . import calendar_config
from .db import get_conn

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 6
_BATCH_SIZE = 25

# The service object is built lazily and reused; discovery does network I/O.
_service = None
_service_lock = threading.Lock()


class CalendarUnavailable(RuntimeError):
    """Raised when the integration cannot talk to Google at all."""


def _build_service():
    global _service
    with _service_lock:
        if _service is not None:
            return _service

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise CalendarUnavailable(
                'google-api-python-client and google-auth are not installed'
            ) from exc

        path = calendar_config.credentials_file()
        if not os.path.isfile(path):
            raise CalendarUnavailable(f'Service account file not found: {path}')

        credentials = service_account.Credentials.from_service_account_file(
            path, scopes=['https://www.googleapis.com/auth/calendar.events']
        )
        # cache_discovery=False avoids the oauth2client file cache warning.
        _service = build('calendar', 'v3', credentials=credentials, cache_discovery=False)
        return _service


def _describe_meal(meal: Dict[str, Any]) -> str:
    lines: List[str] = []

    ingredients = meal.get('ingredients') or []
    if ingredients:
        lines.append('Ingredientes:')
        for ingredient in ingredients:
            spec = ingredient.get('spec')
            lines.append(f"- {ingredient['nombre']}" + (f' ({spec})' if spec else ''))

    steps = meal.get('steps') or []
    if steps:
        if lines:
            lines.append('')
        lines.append('Pasos:')
        for step in steps:
            lines.append(f"{step['orden']}. {step['texto']}")

    categories = meal.get('categories') or []
    if categories:
        if lines:
            lines.append('')
        lines.append('Categorías: ' + ', '.join(c['nombre'] for c in categories))

    return '\n'.join(lines)


def _desired_event(mes: int, año: int, dia: int, slot: str) -> Optional[Dict[str, Any]]:
    """The event this slot should have, or None if it should have none."""
    from . import crud

    window = calendar_config.slot_window(mes, año, dia, slot)
    if window is None:
        return None

    column = calendar_config.SLOT_MEAL_COLUMN[slot]
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            f'SELECT {column} AS meal_id FROM daily_menu WHERE mes = ? AND año = ? AND dia = ?',
            (mes, año, dia)
        )
        row = cur.fetchone()

    if not row or not row['meal_id']:
        return None

    meal = crud.obtener_comida(row['meal_id'])
    if not meal:
        return None

    start, end = window
    timezone = calendar_config.timezone_name()
    return {
        'summary': f"{calendar_config.SLOT_LABEL[slot]}: {meal['nombre']}",
        'description': _describe_meal(meal),
        'start': {'dateTime': start.isoformat(), 'timeZone': timezone},
        'end': {'dateTime': end.isoformat(), 'timeZone': timezone},
        'extendedProperties': {
            'private': {
                'homeapi_slot': slot,
                'homeapi_date': f'{año:04d}-{mes:02d}-{dia:02d}',
                'homeapi_meal_id': str(meal['id']),
            }
        },
    }


def _content_hash(event: Dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(event, sort_keys=True, ensure_ascii=False).encode('utf-8')
    ).hexdigest()


def _stored_event(cur, mes: int, año: int, dia: int, slot: str) -> Optional[Dict[str, Any]]:
    cur.execute('''
        SELECT google_event_id, content_hash
        FROM calendar_events
        WHERE mes = ? AND año = ? AND dia = ? AND slot = ?
    ''', (mes, año, dia, slot))
    row = cur.fetchone()
    return dict(row) if row else None


def sync_slot(mes: int, año: int, dia: int, slot: str) -> str:
    """Reconcile one slot with Google. Returns what was done.

    One of: 'created', 'updated', 'deleted', 'unchanged', 'noop'.
    """
    service = _build_service()
    calendar_id = calendar_config.calendar_id()
    desired = _desired_event(mes, año, dia, slot)

    with get_conn() as conn:
        cur = conn.cursor()
        stored = _stored_event(cur, mes, año, dia, slot)

        if desired is None:
            if not stored:
                return 'noop'
            try:
                service.events().delete(
                    calendarId=calendar_id, eventId=stored['google_event_id']
                ).execute()
            except Exception as exc:
                # A already-gone event (404/410) is the state we want anyway.
                if _http_status(exc) not in (404, 410):
                    raise
            cur.execute('''
                DELETE FROM calendar_events
                WHERE mes = ? AND año = ? AND dia = ? AND slot = ?
            ''', (mes, año, dia, slot))
            conn.commit()
            return 'deleted'

        new_hash = _content_hash(desired)
        if stored and stored['content_hash'] == new_hash:
            return 'unchanged'

        if stored:
            try:
                service.events().update(
                    calendarId=calendar_id,
                    eventId=stored['google_event_id'],
                    body=desired,
                ).execute()
                cur.execute('''
                    UPDATE calendar_events
                    SET content_hash = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE mes = ? AND año = ? AND dia = ? AND slot = ?
                ''', (new_hash, mes, año, dia, slot))
                conn.commit()
                return 'updated'
            except Exception as exc:
                if _http_status(exc) not in (404, 410):
                    raise
                # Someone deleted the event on Google's side: fall through and
                # create a fresh one instead of failing forever.
                cur.execute('''
                    DELETE FROM calendar_events
                    WHERE mes = ? AND año = ? AND dia = ? AND slot = ?
                ''', (mes, año, dia, slot))
                conn.commit()

        created = service.events().insert(calendarId=calendar_id, body=desired).execute()
        cur.execute('''
            INSERT INTO calendar_events (mes, año, dia, slot, google_event_id, content_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(mes, año, dia, slot) DO UPDATE SET
                google_event_id = excluded.google_event_id,
                content_hash = excluded.content_hash,
                updated_at = CURRENT_TIMESTAMP
        ''', (mes, año, dia, slot, created['id'], new_hash))
        conn.commit()
        return 'created'


def _http_status(exc: Exception) -> Optional[int]:
    status = getattr(getattr(exc, 'resp', None), 'status', None)
    try:
        return int(status) if status is not None else None
    except (TypeError, ValueError):
        return None


def _claim_due_slots(limit: int = _BATCH_SIZE) -> List[Tuple[int, int, int, int, str, int]]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT id, mes, año, dia, slot, attempts
            FROM calendar_sync_queue
            WHERE next_attempt_at <= CURRENT_TIMESTAMP
            ORDER BY next_attempt_at
            LIMIT ?
        ''', (limit,))
        return [
            (r['id'], r['mes'], r['año'], r['dia'], r['slot'], r['attempts'])
            for r in cur.fetchall()
        ]


def _mark_done(entry_id: int):
    with get_conn() as conn:
        conn.execute('DELETE FROM calendar_sync_queue WHERE id = ?', (entry_id,))
        conn.commit()


def _mark_failed(entry_id: int, attempts: int, error: str):
    """Exponential backoff, capped, then the entry is dropped as unrecoverable."""
    attempts += 1
    if attempts >= MAX_ATTEMPTS:
        logger.error('Calendar sync giving up on queue entry %s after %s attempts: %s',
                     entry_id, attempts, error)
        _mark_done(entry_id)
        return

    delay_seconds = min(3600, 30 * (2 ** (attempts - 1)))
    with get_conn() as conn:
        conn.execute(f'''
            UPDATE calendar_sync_queue
            SET attempts = ?,
                last_error = ?,
                next_attempt_at = datetime(CURRENT_TIMESTAMP, '+{delay_seconds} seconds')
            WHERE id = ?
        ''', (attempts, error[:500], entry_id))
        conn.commit()


def drain_queue(limit: int = _BATCH_SIZE) -> Dict[str, int]:
    """Process every due queue entry. Returns a count per outcome."""
    counters: Dict[str, int] = {}
    for entry_id, mes, año, dia, slot, attempts in _claim_due_slots(limit):
        try:
            outcome = sync_slot(mes, año, dia, slot)
            _mark_done(entry_id)
        except CalendarUnavailable:
            # Misconfiguration, not a transient failure: stop the whole batch
            # rather than burning every entry's retry budget.
            raise
        except Exception as exc:
            logger.warning('Calendar sync failed for %s-%s-%s %s: %s', año, mes, dia, slot, exc)
            _mark_failed(entry_id, attempts, str(exc))
            outcome = 'failed'
        counters[outcome] = counters.get(outcome, 0) + 1
    return counters


def enqueue_month(mes: int, año: int) -> int:
    """Queue every stored day of a month, for backfill or reconciliation.

    Also queues days that only exist in calendar_events, so events whose
    daily_menu row vanished get cleaned up.
    """
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT dia FROM daily_menu WHERE mes = ? AND año = ?', (mes, año))
        days = {row['dia'] for row in cur.fetchall()}
        cur.execute('SELECT dia FROM calendar_events WHERE mes = ? AND año = ?', (mes, año))
        days |= {row['dia'] for row in cur.fetchall()}

        for dia in sorted(days):
            for slot in calendar_config.SLOTS:
                cur.execute('''
                    INSERT INTO calendar_sync_queue (mes, año, dia, slot)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(mes, año, dia, slot) DO UPDATE SET
                        attempts = 0,
                        last_error = NULL,
                        next_attempt_at = CURRENT_TIMESTAMP
                ''', (mes, año, dia, slot))
        conn.commit()
        return len(days) * len(calendar_config.SLOTS)


def queue_status() -> Dict[str, Any]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) AS total FROM calendar_sync_queue')
        pending = cur.fetchone()['total']
        cur.execute('SELECT COUNT(*) AS total FROM calendar_events')
        published = cur.fetchone()['total']
        cur.execute('''
            SELECT mes, año, dia, slot, attempts, last_error
            FROM calendar_sync_queue
            WHERE last_error IS NOT NULL
            ORDER BY attempts DESC
            LIMIT 10
        ''')
        failures = [dict(row) for row in cur.fetchall()]

    return {
        'enabled': calendar_config.is_enabled(),
        'calendar_id': calendar_config.calendar_id() or None,
        'pending': pending,
        'published_events': published,
        'recent_failures': failures,
    }


# ==================== WORKER EN BACKGROUND ====================
_stop_event = threading.Event()
_worker: Optional[threading.Thread] = None


def _worker_loop():
    poll_seconds = calendar_config.worker_poll_seconds()
    while not _stop_event.is_set():
        try:
            drain_queue()
        except CalendarUnavailable as exc:
            # Back off hard: nothing will succeed until the config is fixed.
            logger.error('Calendar integration unavailable: %s', exc)
            _stop_event.wait(300)
            continue
        except Exception:
            logger.exception('Unexpected error in calendar sync worker')
        _stop_event.wait(poll_seconds)


def start_worker():
    global _worker
    if not calendar_config.is_enabled():
        logger.info('Google Calendar sync disabled; worker not started')
        return
    if _worker and _worker.is_alive():
        return
    _stop_event.clear()
    _worker = threading.Thread(target=_worker_loop, name='calendar-sync', daemon=True)
    _worker.start()
    logger.info('Google Calendar sync worker started (calendar %s)', calendar_config.calendar_id())


def stop_worker():
    _stop_event.set()
    if _worker and _worker.is_alive():
        _worker.join(timeout=5)


def _sleep(seconds: float):  # pragma: no cover - kept for tests to patch
    time_module.sleep(seconds)
