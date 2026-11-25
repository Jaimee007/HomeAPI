#!/usr/bin/env python3
"""End-to-end check of the calendar sync against a REAL Google calendar.

Unlike test_calendar_sync.py (which fakes Google entirely), this drives the real
API: it creates a meal, assigns it to a day, and verifies the event actually
appears, updates and disappears on the calendar.

It uses a throwaway SQLite database, so the real HomeAPI data is never touched.
Every event it creates is deleted again on the way out, including after a
failure. Events are placed far in the future to keep them out of the way.

Usage:
    python scripts/calendar_e2e_check.py --calendar-id <id>
"""

import argparse
import os
import shutil
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# A year far enough out that it cannot collide with a real menu.
TEST_YEAR = 2099
TEST_MONTH = 7

results = []


def check(name, condition, detail=''):
    results.append((name, bool(condition)))
    mark = '[OK]  ' if condition else '[FAIL]'
    print(f'  {mark} {name}' + (f' -- {detail}' if detail and not condition else ''))
    return bool(condition)


def local_time_of(event):
    """Wall-clock time of an event start.

    Google echoes the start back with the zone offset applied
    ('2099-07-05T14:00:00+02:00'), so compare the parsed time rather than
    matching the string.
    """
    return datetime.fromisoformat(event['start']['dateTime']).strftime('%H:%M')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--calendar-id', default=os.getenv('GOOGLE_CALENDAR_ID', ''))
    parser.add_argument('--credentials', default=os.getenv(
        'GOOGLE_SERVICE_ACCOUNT_FILE', os.path.join('secrets', 'google-service-account.json')))
    args = parser.parse_args()

    if not args.calendar_id.strip():
        print('A calendar ID is required: --calendar-id <id>')
        return 2

    workdir = tempfile.mkdtemp(prefix='homeapi_e2e_')
    os.environ['DB_PATH'] = os.path.join(workdir, 'e2e.db')
    os.environ['GOOGLE_CALENDAR_ENABLED'] = '1'
    os.environ['GOOGLE_CALENDAR_ID'] = args.calendar_id.strip()
    os.environ['GOOGLE_SERVICE_ACCOUNT_FILE'] = args.credentials

    from app import calendar_sync, crud
    from app.db import init_database

    print('=' * 68)
    print('HomeAPI - end-to-end calendar check (real Google calendar)')
    print('=' * 68)
    print(f'Calendar:    {args.calendar_id.strip()}')
    print(f'Scratch DB:  {os.environ["DB_PATH"]}')
    print(f'Test dates:  {TEST_MONTH}/{TEST_YEAR}')

    init_database()
    service = calendar_sync._build_service()
    calendar_id = args.calendar_id.strip()
    created_ids = set()

    def remote(event_id):
        """Fetch an event from Google, or None if it is gone."""
        try:
            event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            return None if event.get('status') == 'cancelled' else event
        except Exception:
            return None

    def stored_event_id(dia, slot):
        from app.db import get_conn
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute('''
                SELECT google_event_id FROM calendar_events
                WHERE mes = ? AND año = ? AND dia = ? AND slot = ?
            ''', (TEST_MONTH, TEST_YEAR, dia, slot))
            row = cur.fetchone()
            return row['google_event_id'] if row else None

    try:
        # --- 1. Assigning a meal publishes an event -----------------------
        print('\n1. Assigning a meal to a day publishes an event')
        meal = crud.crear_comida(
            'E2E Lentejas',
            [],
            [],
            ['Poner las lentejas en remojo', 'Cocer 40 minutos', 'Servir caliente'],
        )
        day = crud.crear_dia_menu(TEST_MONTH, TEST_YEAR, 5, meal['id'], None)
        outcomes = calendar_sync.drain_queue()
        check('sync reported one event created', outcomes.get('created') == 1, str(outcomes))

        lunch_id = stored_event_id(5, 'lunch')
        if lunch_id:
            created_ids.add(lunch_id)
        check('event id recorded locally', bool(lunch_id))

        event = remote(lunch_id) if lunch_id else None
        check('event exists on the real calendar', event is not None)
        if event:
            check('title names the slot and the meal',
                  event.get('summary') == 'Comida: E2E Lentejas', event.get('summary'))
            check('starts at 14:00 local time',
                  local_time_of(event) == '14:00', event['start']['dateTime'])
            check('timezone is Europe/Madrid',
                  event['start'].get('timeZone') == 'Europe/Madrid', str(event['start']))
            check('description carries the numbered steps',
                  '1. Poner las lentejas en remojo' in (event.get('description') or ''),
                  repr(event.get('description'))[:120])
            check('date is the assigned day',
                  event['start']['dateTime'].startswith(f'{TEST_YEAR}-07-05'),
                  event['start']['dateTime'])

        # --- 2. Editing the meal updates the same event -------------------
        print('\n2. Editing the meal updates the existing event (no duplicate)')
        ingredient = crud.crear_ingrediente('E2E Lentejas pardinas')
        crud.actualizar_comida(
            meal['id'],
            nombre='E2E Lentejas con chorizo',
            ingredient_entries=[{'ingredient_id': ingredient['id'], 'spec': '400 g'}],
        )
        outcomes = calendar_sync.drain_queue()
        check('sync reported an update', outcomes.get('updated') == 1, str(outcomes))
        check('event id unchanged', stored_event_id(5, 'lunch') == lunch_id)

        event = remote(lunch_id)
        check('title reflects the new name',
              event and event.get('summary') == 'Comida: E2E Lentejas con chorizo',
              event.get('summary') if event else 'missing')
        check('description now lists the ingredient with its quantity',
              event and 'E2E Lentejas pardinas (400 g)' in (event.get('description') or ''),
              repr(event.get('description'))[:160] if event else 'missing')

        # --- 3. Nothing changed means no API call -------------------------
        print('\n3. Re-syncing an unchanged day costs no API call')
        calendar_sync.enqueue_month(TEST_MONTH, TEST_YEAR)
        outcomes = calendar_sync.drain_queue()
        check('reported as unchanged', outcomes.get('unchanged') == 1, str(outcomes))

        # --- 4. A dinner on the same day is a separate event --------------
        print('\n4. Adding a dinner creates a second, separate event')
        dinner = crud.crear_comida('E2E Sopa', [], [], [])
        crud.actualizar_dia_menu(day['id'], meal_lunch_id=meal['id'], meal_dinner_id=dinner['id'])
        outcomes = calendar_sync.drain_queue()
        check('one new event created', outcomes.get('created') == 1, str(outcomes))

        dinner_id = stored_event_id(5, 'dinner')
        if dinner_id:
            created_ids.add(dinner_id)
        check('dinner is a distinct event', dinner_id and dinner_id != lunch_id)
        dinner_event = remote(dinner_id) if dinner_id else None
        check('dinner starts at 21:00 local time',
              dinner_event and local_time_of(dinner_event) == '21:00',
              dinner_event['start']['dateTime'] if dinner_event else 'missing')
        check('dinner title uses the Cena label',
              dinner_event and dinner_event.get('summary') == 'Cena: E2E Sopa',
              dinner_event.get('summary') if dinner_event else 'missing')
        check('lunch event still there', remote(lunch_id) is not None)

        # --- 5. Clearing a slot deletes only that event -------------------
        print('\n5. Clearing the dinner deletes only the dinner event')
        crud.actualizar_dia_menu(day['id'], meal_lunch_id=meal['id'], meal_dinner_id=None)
        outcomes = calendar_sync.drain_queue()
        check('sync reported a deletion', outcomes.get('deleted') == 1, str(outcomes))
        check('dinner event gone from the calendar', remote(dinner_id) is None)
        check('lunch event untouched', remote(lunch_id) is not None)
        if dinner_id:
            created_ids.discard(dinner_id)

        # --- 6. Deleting the meal cleans up every day using it ------------
        print('\n6. Deleting the meal removes the events of every day using it')
        crud.crear_dia_menu(TEST_MONTH, TEST_YEAR, 6, meal['id'], None)
        calendar_sync.drain_queue()
        second_id = stored_event_id(6, 'lunch')
        if second_id:
            created_ids.add(second_id)
        check('second day published', remote(second_id) is not None if second_id else False)

        crud.eliminar_comida(meal['id'])
        calendar_sync.drain_queue()
        check('first day event removed', remote(lunch_id) is None)
        check('second day event removed', remote(second_id) is None if second_id else False)
        check('no local mappings left',
              stored_event_id(5, 'lunch') is None and stored_event_id(6, 'lunch') is None)
        created_ids.discard(lunch_id)
        if second_id:
            created_ids.discard(second_id)

        # --- 7. The worker thread does the same unattended ----------------
        print('\n7. The background worker publishes without being driven by hand')
        import time
        calendar_sync.start_worker()
        try:
            worker_meal = crud.crear_comida('E2E Worker Paella', [], [], [])
            crud.crear_dia_menu(TEST_MONTH, TEST_YEAR, 7, worker_meal['id'], None)
            worker_event_id = None
            for _ in range(60):
                worker_event_id = stored_event_id(7, 'lunch')
                if worker_event_id:
                    break
                time.sleep(0.5)
            if worker_event_id:
                created_ids.add(worker_event_id)
            check('worker published the event unattended', bool(worker_event_id))
            check('event is on the calendar',
                  remote(worker_event_id) is not None if worker_event_id else False)
            check('queue drained by the worker', calendar_sync.queue_status()['pending'] == 0,
                  str(calendar_sync.queue_status()['pending']))
        finally:
            calendar_sync.stop_worker()

    finally:
        # --- cleanup ------------------------------------------------------
        print('\n8. Cleanup')
        leftovers = []
        for event_id in sorted(created_ids):
            try:
                service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            except Exception as exc:
                status = getattr(getattr(exc, 'resp', None), 'status', None)
                if status not in (404, 410):
                    leftovers.append(f'{event_id}: {exc}')
        check('every test event removed from the calendar', not leftovers, '; '.join(leftovers))

        # Belt and braces: sweep the test window for anything named E2E.
        try:
            found = service.events().list(
                calendarId=calendar_id,
                timeMin=f'{TEST_YEAR}-07-01T00:00:00Z',
                timeMax=f'{TEST_YEAR}-08-01T00:00:00Z',
                maxResults=50,
            ).execute().get('items', [])
            stragglers = [e for e in found if 'E2E' in (e.get('summary') or '')]
            for straggler in stragglers:
                service.events().delete(calendarId=calendar_id, eventId=straggler['id']).execute()
            check('no test events left in the test window', True,
                  f'swept {len(stragglers)}' if stragglers else '')
            if stragglers:
                print(f'       (swept {len(stragglers)} extra event(s))')
        except Exception as exc:
            check('could sweep the test window', False, str(exc))

        shutil.rmtree(workdir, ignore_errors=True)
        print(f'       Scratch database removed')

    failed = [name for name, passed in results if not passed]
    print('\n' + '=' * 68)
    print(f'{len(results) - len(failed)}/{len(results)} checks passed')
    for name in failed:
        print(f'  FAILED: {name}')
    print('=' * 68)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
