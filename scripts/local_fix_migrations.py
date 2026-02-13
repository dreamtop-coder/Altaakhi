"""Safe local fixer for mixed original + squashed django migrations.

Usage (dry-run):
    venv/Scripts/python.exe scripts/local_fix_migrations.py --dry-run
To apply inserts after review:
    venv/Scripts/python.exe scripts/local_fix_migrations.py --apply --yes

Behavior:
- Backs up ``db.sqlite3`` (when --apply).
- Uses Django's :class:`django.db.migrations.loader.MigrationLoader` to compare
    on-disk migrations vs applied rows.
- Finds squashed migrations (``migration.replaces`` is present) that are not
    recorded in ``django_migrations`` but whose replaced migrations ARE recorded.
- Inserts rows for those squashed migrations into ``django_migrations`` in a
    safe order and prints a clear summary.

IMPORTANT: This is a surgical tool for local recovery only. Always backup
before ``--apply``.
"""

import argparse
import datetime
import os
import sqlite3
import sys

# Ensure the project root is on sys.path so Django can import the project
# when this script is executed directly (e.g. ``python scripts/local_fix_migrations.py``).
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')

import django
from django.db import connection
from django.db.migrations.loader import MigrationLoader


def iso_now():
    return datetime.datetime.utcnow().isoformat()


def get_applied_migrations(conn):
    cur = conn.cursor()
    cur.execute("SELECT app, name FROM django_migrations")
    return set(cur.fetchall())


def run(dry_run=True, do_apply=False, yes=False):
    # Ensure Django can import project
    try:
        django.setup()
    except Exception as e:
        print('ERROR: django.setup() failed:', e)
        sys.exit(1)

    conn = sqlite3.connect('db.sqlite3')
    applied = get_applied_migrations(conn)

    loader = MigrationLoader(connection)
    disk = loader.disk_migrations  # mapping (app,label) -> Migration object

    # Find squashed migrations not present in django_migrations where all replaced migrations are present
    candidates = []
    for key, mig in disk.items():
        if getattr(mig, 'replaces', None):
            if key in applied:
                continue
            # mig.replaces is list of (app,name) tuples
            replaced = set(mig.replaces)
            if replaced.issubset(applied):
                candidates.append((key, mig, replaced))

    if not candidates:
        print('No safe squashed migrations to insert. Nothing to do.')
        return 0

    print('Found candidate squashed migrations to record:')
    for key, mig, replaced in candidates:
        print(f' - {key[0]}.{key[1]} replaces {sorted(list(replaced))}')

    if dry_run:
        print('\nDRY-RUN: no DB changes will be made. Re-run with --apply to insert rows.')
        return 0

    # apply path
    if not yes:
        confirm = input('\nApply these inserts to db.sqlite3? Type yes to continue: ')
        if confirm.strip().lower() != 'yes':
            print('Aborted by user.')
            return 1

    # backup
    bak = f"db.sqlite3.localfix_bak_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    import shutil
    shutil.copy('db.sqlite3', bak)
    print('DB backed up to', bak)

    cur = conn.cursor()
    inserted = []
    for (app, name), mig, replaced in candidates:
        now = iso_now()
        print('Inserting', (app, name))
        cur.execute('INSERT INTO django_migrations(app, name, applied) VALUES (?,?,?)', (app, name, now))
        inserted.append((app, name))
    conn.commit()

    if inserted:
        print('\nInserted rows:')
        for r in inserted:
            print(' -', r)
    else:
        print('No rows inserted.')

    return 0


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--dry-run', action='store_true', help='Only show candidate inserts (default)')
    p.add_argument('--apply', action='store_true', help='Perform DB inserts')
    p.add_argument('--yes', action='store_true', help='Auto-confirm prompts')
    args = p.parse_args()

    if args.apply:
        sys.exit(run(dry_run=False, do_apply=True, yes=args.yes))
    else:
        sys.exit(run(dry_run=True))
