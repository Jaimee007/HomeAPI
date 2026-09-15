#!/usr/bin/env python3
"""Diagnose the Google Calendar setup without starting the API.

Validates the credentials file, authenticates, lists the calendars the service
account can reach (so it can tell you the calendar ID you need), and optionally
round-trips a throwaway event to prove write access.

Usage:
    python scripts/calendar_check.py
    python scripts/calendar_check.py --calendar-id c_abc@group.calendar.google.com
    python scripts/calendar_check.py --calendar-id ... --write-test

Reads GOOGLE_SERVICE_ACCOUNT_FILE and GOOGLE_CALENDAR_ID when the flags are
omitted. It never touches the HomeAPI database.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCOPES = ['https://www.googleapis.com/auth/calendar.events']
# Listing calendars needs a broader read scope than publishing events does.
LIST_SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def fail(message, hint=''):
    print(f'\n[FAIL] {message}')
    if hint:
        print(f'       {hint}')
    return False


def ok(message):
    print(f'[OK]   {message}')
    return True


def http_status(exc):
    return getattr(getattr(exc, 'resp', None), 'status', None)


def check_credentials_file(path):
    print(f'\n1. Credentials file: {path}')
    if not os.path.isfile(path):
        return fail('File not found.',
                    'Download the service account JSON key and place it there, '
                    'or pass --credentials with the right path.')
    try:
        with open(path, encoding='utf-8') as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        return fail(f'Not valid JSON: {exc}', 'Re-download the key from the Cloud console.')

    if data.get('type') != 'service_account':
        return fail(f"Wrong credential type: {data.get('type')!r}.",
                    'You downloaded an OAuth client secret, not a service account key. '
                    'Create credentials of type "Service account" instead.')

    for field in ('client_email', 'private_key', 'project_id'):
        if not data.get(field):
            return fail(f'Key is missing the {field!r} field.', 'Re-download it.')

    ok(f"Valid service account key for project {data['project_id']}")
    print(f"       Service account email: {data['client_email']}")
    print('       ^ this is the address the calendar must be shared with')
    return data['client_email']


def build_service(path, scopes):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    credentials = service_account.Credentials.from_service_account_file(path, scopes=scopes)
    return build('calendar', 'v3', credentials=credentials, cache_discovery=False)


def check_auth(path):
    print('\n2. Authentication')
    try:
        service = build_service(path, SCOPES)
        ok('Credentials loaded and Calendar API client built')
        return service
    except Exception as exc:
        fail(f'Could not authenticate: {exc}')
        return None


def list_calendars(path):
    """List the service account's own calendarList, for information only.

    A calendar shared with a service account does NOT appear here. That list is
    the equivalent of the sidebar and is populated by accepting an emailed
    invitation, which a service account can never do. So an empty list is normal
    and says nothing about whether the sharing worked -- only a direct call with
    the calendar ID can tell us that.
    """
    print('\n3. Calendars in the service account own list (informational)')
    try:
        service = build_service(path, LIST_SCOPES)
        entries = service.calendarList().list().execute().get('items', [])
    except Exception as exc:
        status = http_status(exc)
        if status == 403:
            fail('403 Forbidden listing calendars.',
                 'Enable the Google Calendar API for the project: Cloud console -> '
                 'APIs & Services -> Library -> Google Calendar API -> Enable.')
        else:
            fail(f'Could not list calendars: {exc}')
        return []

    if not entries:
        print('       Empty, which is expected: a shared calendar never shows up here.')
        print('       Verification needs the calendar ID (step 4).')
        return []

    for entry in entries:
        writable = entry.get('accessRole') in ('writer', 'owner')
        mark = 'writable' if writable else f"read-only ({entry.get('accessRole')})"
        print(f"  - {entry.get('summary', '(no name)')}")
        print(f"      id:     {entry['id']}")
        print(f"      access: {mark}")
        print(f"      tz:     {entry.get('timeZone', '?')}")
    return entries


def check_calendar_access(service, calendar_id):
    """The real verification: address the calendar by ID, sharing or not.

    Uses events().list rather than calendars().get on purpose: under the narrow
    calendar.events scope the app actually holds, calendars().get returns 403
    even when the calendar is perfectly reachable. Probing with the call the app
    really makes avoids diagnosing a failure the app would never hit.
    """
    print(f'\n4. Access to calendar {calendar_id}')
    try:
        service.events().list(calendarId=calendar_id, maxResults=1).execute()
        return ok('The service account can read this calendar events')
    except Exception as exc:
        status = http_status(exc)
        if status in (403, 404):
            # Google returns the same answer for "no such calendar" and "not
            # shared with you", so it cannot tell the two apart for us.
            return fail(f'{status}: the service account cannot reach this calendar.',
                        'Check, in this order: (1) the calendar ID is copied exactly from '
                        'Settings and sharing -> Integrate calendar; (2) that calendar is '
                        'shared with the service account email under "Share with specific '
                        'people or groups"; (3) the share has saved - reopen the settings '
                        'page and confirm the address is listed.')
        return fail(f'Unexpected error: {exc}')


def write_test(service, calendar_id, timezone):
    print('\n5. Write test (creates and deletes a temporary event)')
    start = datetime.now().replace(microsecond=0) + timedelta(days=400)
    body = {
        'summary': 'HomeAPI connection test - safe to ignore',
        'description': 'Created by scripts/calendar_check.py. It deletes itself immediately.',
        'start': {'dateTime': start.isoformat(), 'timeZone': timezone},
        'end': {'dateTime': (start + timedelta(minutes=30)).isoformat(), 'timeZone': timezone},
    }

    try:
        created = service.events().insert(calendarId=calendar_id, body=body).execute()
    except Exception as exc:
        status = http_status(exc)
        if status == 403:
            return fail('403 Forbidden creating an event.',
                        'The calendar is shared read-only. Change the permission to '
                        '"Make changes to events".')
        return fail(f'Could not create an event: {exc}')

    event_id = created['id']
    ok(f'Event created ({event_id})')

    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        ok('Event deleted - the calendar is clean again')
    except Exception as exc:
        return fail(f'Created the event but could not delete it: {exc}',
                    f'Remove "{body["summary"]}" from the calendar by hand.')
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--credentials', default=os.getenv(
        'GOOGLE_SERVICE_ACCOUNT_FILE', os.path.join('secrets', 'google-service-account.json')))
    parser.add_argument('--calendar-id', default=os.getenv('GOOGLE_CALENDAR_ID', ''))
    parser.add_argument('--timezone', default=os.getenv('CALENDAR_TIMEZONE', 'Europe/Madrid'))
    parser.add_argument('--write-test', action='store_true',
                        help='also create and delete a temporary event')
    args = parser.parse_args()

    print('=' * 64)
    print('HomeAPI - Google Calendar setup check')
    print('=' * 64)

    if not check_credentials_file(args.credentials):
        return 1

    service = check_auth(args.credentials)
    if service is None:
        return 1

    entries = list_calendars(args.credentials)

    calendar_id = args.calendar_id.strip()
    if not calendar_id:
        print('\n' + '-' * 64)
        print('No calendar ID given, so nothing could be verified.')
        writable = [e for e in entries if e.get('accessRole') in ('writer', 'owner')]
        if len(writable) == 1:
            print('\nUse this one - the only writable calendar in the list above:')
            print(f"\n  GOOGLE_CALENDAR_ID={writable[0]['id']}")
            print('\nThen re-run with:')
            print(f"  python scripts/calendar_check.py --calendar-id {writable[0]['id']} --write-test")
        else:
            print('\nFind the ID in Google Calendar: hover the calendar in the sidebar -> the')
            print('three-dot menu -> Settings and sharing -> scroll to "Integrate calendar" ->')
            print('copy "Calendar ID". It looks like c_abc123@group.calendar.google.com')
            print('(for your main calendar it is just your Gmail address).')
            print('\nThen re-run with:')
            print('  python scripts/calendar_check.py --calendar-id <id> --write-test')
        print('-' * 64)
        return 1

    if not check_calendar_access(service, calendar_id):
        return 1

    if args.write_test and not write_test(service, calendar_id, args.timezone):
        return 1

    print('\n' + '=' * 64)
    print('Setup looks good.')
    print(f'  GOOGLE_CALENDAR_ENABLED=1')
    print(f'  GOOGLE_CALENDAR_ID={calendar_id}')
    if not args.write_test:
        print('\nRe-run with --write-test to also verify write access.')
    print('=' * 64)
    return 0


if __name__ == '__main__':
    sys.exit(main())
