"""Repair helpers for local django migration history (safe, dry-run first).

This script helps identify and optionally remove confusing rows from
the ``django_migrations`` table. It is intentionally conservative: by
default it only suggests deleting original migrations that were
replaced by a squashed migration (i.e. where a squashed migration
exists on-disk and the original migrations are still recorded as
applied). Use ``--delete-missing`` to also remove applied rows that
have no corresponding on-disk migration file.

Usage (dry-run):
  venv/Scripts/python.exe scripts/repair_django_migrations.py --dry-run

To apply changes (will backup DB):
  venv/Scripts/python.exe scripts/repair_django_migrations.py --apply --yes

This script only supports SQLite (local developer DB). For other
engines use DB-specific tools.
"""

import argparse
import os
import shutil
import sqlite3
import sys

# Ensure project root on path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')

import django
from django.conf import settings
from django.db import connection
from django.db.migrations.loader import MigrationLoader


def get_applied(conn):
    cur = conn.cursor()
    cur.execute("SELECT app, name FROM django_migrations ORDER BY id")
    return [tuple(r) for r in cur.fetchall()]


def run(dry_run=True, do_apply=False, yes=False, delete_missing=False):
    try:
        django.setup()
    except Exception as e:
        print('ERROR: django.setup() failed:', e)
        sys.exit(1)

    # Only support sqlite for safe local edits
    db_conf = settings.DATABASES.get('default', {})
    engine = db_conf.get('ENGINE', '')
    name = db_conf.get('NAME')
    if 'sqlite' not in engine.lower():
        print('This script only supports SQLite databases. Aborting.')
        return 2

    db_path = name or 'db.sqlite3'
    if not os.path.exists(db_path):
        print('Database file not found:', db_path)
        return 2

    conn = sqlite3.connect(db_path)

    loader = MigrationLoader(connection)
    disk_keys = set(loader.disk_migrations.keys())
    applied = get_applied(conn)
    applied_set = set(applied)

    # Replacements mapping: (app,label) -> list of replaced (app,label)
    replacements = getattr(loader, 'replacements', {}) or {}

    candidates_delete_originals = []
    for squashed_key, replacement_val in replacements.items():
        # replacement_val may be a list of tuples or a Migration object with
        # a ``replaces`` attribute. Normalise to an iterable of (app,name).
        replaced_list = None
        if hasattr(replacement_val, 'replaces'):
            replaced_list = getattr(replacement_val, 'replaces') or []
        else:
            replaced_list = replacement_val or []
        # if squashed exists on disk (or applied) and any replaced are applied,
        # the originals are confusing and are candidates for deletion.
        if squashed_key in disk_keys or squashed_key in applied_set:
            for r in replaced_list:
                rr = tuple(r)
                if rr in applied_set:
                    candidates_delete_originals.append(rr)

    candidates_delete_missing = []
    if delete_missing:
        for a in applied:
            if tuple(a) not in disk_keys and tuple(a) not in replacements:
                # applied but no file on disk and not part of a replacement mapping
                candidates_delete_missing.append(tuple(a))

    if not candidates_delete_originals and not candidates_delete_missing:
        print('No safe candidates found for deletion (use --delete-missing to include missing files).')
        return 0

    print('Candidates to delete (originals replaced by squashed migrations):')
    for c in sorted(set(candidates_delete_originals)):
        print(' -', c)
    if delete_missing:
        print('\nCandidates to delete (applied but no on-disk file):')
        for c in sorted(set(candidates_delete_missing)):
            print(' -', c)

    if dry_run:
        print('\nDRY-RUN: no changes will be made. Re-run with --apply to perform deletions.')
        return 0

    # confirm
    if not yes:
        confirm = input('\nApply these deletions to %s? Type yes to continue: ' % db_path)
        if confirm.strip().lower() != 'yes':
            print('Aborted by user.')
            return 1

    # Backup
    bak = db_path + '.repair_bak'
    shutil.copy(db_path, bak)
    print('DB backed up to', bak)

    cur = conn.cursor()
    deleted = []
    for app, name in sorted(set(candidates_delete_originals)):
        print('Deleting', (app, name))
        cur.execute('DELETE FROM django_migrations WHERE app=? AND name=?', (app, name))
        deleted.append((app, name))
    if delete_missing:
        for app, name in sorted(set(candidates_delete_missing)):
            print('Deleting (missing file)', (app, name))
            cur.execute('DELETE FROM django_migrations WHERE app=? AND name=?', (app, name))
            deleted.append((app, name))
    conn.commit()

    print('\nDeleted rows:')
    for d in deleted:
        print(' -', d)
    return 0


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--dry-run', action='store_true', help='Show candidate deletions (default)')
    p.add_argument('--apply', action='store_true', help='Perform deletions')
    p.add_argument('--yes', action='store_true', help='Auto-confirm prompts')
    p.add_argument('--delete-missing', action='store_true', help='Also delete applied migrations that have no on-disk file')
    args = p.parse_args()

    if args.apply:
        sys.exit(run(dry_run=False, do_apply=True, yes=args.yes, delete_missing=args.delete_missing))
    else:
        sys.exit(run(dry_run=True, delete_missing=args.delete_missing))
