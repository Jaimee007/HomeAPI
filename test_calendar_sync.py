#!/usr/bin/env python3
"""Tests for the Google Calendar sync logic, with Google itself faked out.

Runs against a throwaway SQLite file: no network, no credentials, no calendar.
Usage: python test_calendar_sync.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure before importing the app so module-level env reads see it.
_tmp_db = os.path.join(tempfile.mkdtemp(prefix='homeapi_caltest_'), 'test.db')
os.environ['DB_PATH'] = _tmp_db
os.environ['GOOGLE_CALENDAR_ENABLED'] = '1'
os.environ['GOOGLE_CALENDAR_ID'] = 'test-calendar@group.calendar.google.com'
os.environ['CALENDAR_LUNCH_TIME'] = '14:00'
os.environ['CALENDAR_DINNER_TIME'] = '21:00'

from app import calendar_config, calendar_sync, crud  # noqa: E402
from app.db import get_conn, init_database  # noqa: E402


class FakeEvents:
    """Stands in for service.events(), recording every call."""

    def __init__(self, store, log):
        self.store = store
        self.log = log
        self.next_id = 1

    def _result(self, value):
        class _Request:
            def execute(_self):
                return value
        return _Request()

    def insert(self, calendarId, body):
        event_id = f'evt{self.next_id}'
        self.next_id += 1
        self.store[event_id] = body
        self.log.append(('insert', event_id, body['summary']))
        return self._result({'id': event_id, **body})

    def update(self, calendarId, eventId, body):
        if eventId not in self.store:
            raise _HttpError(404)
        self.store[eventId] = body
        self.log.append(('update', eventId, body['summary']))
        return self._result({'id': eventId, **body})

    def delete(self, calendarId, eventId):
        if eventId not in self.store:
            raise _HttpError(404)
        del self.store[eventId]
        self.log.append(('delete', eventId, None))
        return self._result({})


class _HttpError(Exception):
    def __init__(self, status):
        super().__init__(f'HTTP {status}')

        class _Resp:
            pass
        self.resp = _Resp()
        self.resp.status = status


class FakeService:
    def __init__(self):
        self.store = {}
        self.log = []
        self._events = FakeEvents(self.store, self.log)

    def events(self):
        return self._events


def _install_fake_service():
    service = FakeService()
    calendar_sync._build_service = lambda: service
    return service


def _pending_count():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) AS total FROM calendar_sync_queue')
        return cur.fetchone()['total']


def _reset_db():
    for path in (_tmp_db, _tmp_db + '-wal', _tmp_db + '-shm'):
        if os.path.exists(path):
            os.remove(path)
    init_database()


results = []


def check(name, condition, detail=''):
    results.append((name, bool(condition), detail))
    print(f"  {'[OK]  ' if condition else '[FAIL]'} {name}" + (f' — {detail}' if detail and not condition else ''))


def test_create_and_update():
    print('\n[TEST] Creating and updating a day publishes and edits events')
    _reset_db()
    service = _install_fake_service()

    meal = crud.crear_comida('Lentejas', [], [], ['Cocer', 'Servir'])
    day = crud.crear_dia_menu(3, 2026, 10, meal['id'], None)

    check('both slots queued on create', _pending_count() == 2, f'pending={_pending_count()}')

    outcomes = calendar_sync.drain_queue()
    check('one event created, one empty slot skipped',
          outcomes.get('created') == 1 and outcomes.get('noop') == 1, str(outcomes))
    check('queue drained', _pending_count() == 0, f'pending={_pending_count()}')

    event = next(iter(service.store.values()))
    check('summary carries slot and meal', event['summary'] == 'Comida: Lentejas', event['summary'])
    # The fake echoes the body back verbatim; the real API applies the zone
    # offset, so parse rather than string-match (see calendar_e2e_check.py).
    from datetime import datetime as _dt
    check('lunch starts at 14:00',
          _dt.fromisoformat(event['start']['dateTime']).strftime('%H:%M') == '14:00',
          event['start']['dateTime'])
    check('description carries the steps', '1. Cocer' in event['description'], event['description'])

    # Renaming the meal must refresh every day that uses it.
    crud.actualizar_comida(meal['id'], nombre='Lentejas con chorizo')
    outcomes = calendar_sync.drain_queue()
    check('rename updates the event', outcomes.get('updated') == 1, str(outcomes))
    event = next(iter(service.store.values()))
    check('updated summary', event['summary'] == 'Comida: Lentejas con chorizo', event['summary'])

    # Re-syncing with nothing changed must not call Google again.
    calendar_sync.enqueue_month(3, 2026)
    outcomes = calendar_sync.drain_queue()
    check('unchanged content is not republished', outcomes.get('unchanged') == 1, str(outcomes))

    return day, meal, service


def test_clearing_a_slot_deletes_the_event():
    print('\n[TEST] Clearing a slot deletes its event')
    _reset_db()
    service = _install_fake_service()

    meal = crud.crear_comida('Sopa', [], [], [])
    day = crud.crear_dia_menu(3, 2026, 11, meal['id'], meal['id'])
    calendar_sync.drain_queue()
    check('two events published', len(service.store) == 2, f'store={len(service.store)}')

    # The PUT always writes both ids, so omitting dinner clears it.
    crud.actualizar_dia_menu(day['id'], meal_lunch_id=meal['id'], meal_dinner_id=None)
    outcomes = calendar_sync.drain_queue()
    check('dinner event deleted', outcomes.get('deleted') == 1, str(outcomes))
    check('only lunch remains', len(service.store) == 1, f'store={len(service.store)}')


def test_deleting_a_meal_cleans_up():
    print('\n[TEST] Deleting a meal removes events from every day using it')
    _reset_db()
    service = _install_fake_service()

    meal = crud.crear_comida('Tortilla', [], [], [])
    crud.crear_dia_menu(3, 2026, 12, meal['id'], None)
    crud.crear_dia_menu(3, 2026, 13, None, meal['id'])
    calendar_sync.drain_queue()
    check('two events published', len(service.store) == 2, f'store={len(service.store)}')

    # ON DELETE SET NULL silently empties both days.
    crud.eliminar_comida(meal['id'])
    check('affected slots queued', _pending_count() == 2, f'pending={_pending_count()}')
    calendar_sync.drain_queue()
    check('no orphaned events left', len(service.store) == 0, f'store={len(service.store)}')


def test_deleting_a_day_removes_its_events():
    print('\n[TEST] Deleting a day removes its events')
    _reset_db()
    service = _install_fake_service()

    meal = crud.crear_comida('Arroz', [], [], [])
    day = crud.crear_dia_menu(3, 2026, 14, meal['id'], None)
    calendar_sync.drain_queue()

    crud.eliminar_dia_menu(day['id'])
    calendar_sync.drain_queue()
    check('event removed with the day', len(service.store) == 0, f'store={len(service.store)}')


def test_impossible_date_is_skipped():
    print('\n[TEST] A date that does not exist publishes nothing')
    _reset_db()
    service = _install_fake_service()

    meal = crud.crear_comida('Paella', [], [], [])
    crud.crear_dia_menu(2, 2026, 31, meal['id'], None)  # 31 February
    outcomes = calendar_sync.drain_queue()
    check('nothing published for 31/02', len(service.store) == 0, str(outcomes))
    check('queue still drained', _pending_count() == 0, f'pending={_pending_count()}')


def test_event_deleted_on_google_is_recreated():
    print('\n[TEST] An event deleted in Google is recreated, not retried forever')
    _reset_db()
    service = _install_fake_service()

    meal = crud.crear_comida('Merluza', [], [], [])
    crud.crear_dia_menu(3, 2026, 15, meal['id'], None)
    calendar_sync.drain_queue()
    check('event published', len(service.store) == 1, f'store={len(service.store)}')

    service.store.clear()  # someone deleted it from the calendar UI
    crud.actualizar_comida(meal['id'], nombre='Merluza al horno')
    outcomes = calendar_sync.drain_queue()
    check('recreated instead of failing', outcomes.get('created') == 1, str(outcomes))
    check('one event present again', len(service.store) == 1, f'store={len(service.store)}')


def test_failure_is_retried_with_backoff():
    print('\n[TEST] A transient Google failure is retried, not lost')
    _reset_db()
    service = _install_fake_service()

    meal = crud.crear_comida('Guiso', [], [], [])
    crud.crear_dia_menu(3, 2026, 16, meal['id'], None)

    def _boom(**kwargs):
        raise RuntimeError('Google is down')
    original_insert = service._events.insert
    service._events.insert = _boom

    outcomes = calendar_sync.drain_queue()
    check('failure recorded', outcomes.get('failed') == 1, str(outcomes))
    check('entry kept for retry', _pending_count() >= 1, f'pending={_pending_count()}')

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute('SELECT attempts, last_error FROM calendar_sync_queue LIMIT 1')
        row = cur.fetchone()
    check('attempt counted', row['attempts'] == 1, f"attempts={row['attempts']}")
    check('error stored', 'Google is down' in (row['last_error'] or ''), str(row['last_error']))

    # Backoff means it is not due yet; force it due and let it succeed.
    service._events.insert = original_insert
    with get_conn() as conn:
        conn.execute('UPDATE calendar_sync_queue SET next_attempt_at = CURRENT_TIMESTAMP')
        conn.commit()
    outcomes = calendar_sync.drain_queue()
    check('retry succeeds', outcomes.get('created') == 1, str(outcomes))


def test_disabled_integration_queues_nothing():
    print('\n[TEST] With the integration off, nothing is queued')
    _reset_db()
    os.environ['GOOGLE_CALENDAR_ENABLED'] = '0'
    try:
        meal = crud.crear_comida('Ensalada', [], [], [])
        crud.crear_dia_menu(3, 2026, 17, meal['id'], None)
        check('queue stays empty', _pending_count() == 0, f'pending={_pending_count()}')
    finally:
        os.environ['GOOGLE_CALENDAR_ENABLED'] = '1'


def main():
    print('=' * 60)
    print('Google Calendar sync tests (no network, no credentials)')
    print('=' * 60)

    test_create_and_update()
    test_clearing_a_slot_deletes_the_event()
    test_deleting_a_meal_cleans_up()
    test_deleting_a_day_removes_its_events()
    test_impossible_date_is_skipped()
    test_event_deleted_on_google_is_recreated()
    test_failure_is_retried_with_backoff()
    test_disabled_integration_queues_nothing()

    failed = [name for name, ok, _ in results if not ok]
    print('\n' + '=' * 60)
    print(f'{len(results) - len(failed)}/{len(results)} checks passed')
    if failed:
        print('FAILED:')
        for name in failed:
            print(f'  - {name}')
    print('=' * 60)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
