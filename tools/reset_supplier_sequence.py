import os
import sys

# Ensure project root is on sys.path so 'workshop' and apps import correctly
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()

from django.db import connection
from inventory.models import Supplier

def main():
    table_name = Supplier._meta.db_table
    print('Supplier table:', table_name)
    print('DB engine:', connection.vendor)
    if connection.vendor != 'sqlite':
        print('Not using SQLite — aborting. This script only resets SQLite sqlite_sequence.')
        return

    cur = connection.cursor()
    try:
        cur.execute("SELECT name, seq FROM sqlite_sequence WHERE name=%s", [table_name])
        rows = cur.fetchall()
        print('sqlite_sequence entry before:', rows)
    except Exception as e:
        print('Could not read sqlite_sequence (maybe table not present):', e)
        rows = None

    if rows:
        try:
            cur.execute("DELETE FROM sqlite_sequence WHERE name=%s", [table_name])
            connection.commit()
            print('Deleted sqlite_sequence entry for', table_name)
        except Exception as e:
            print('Failed to delete sqlite_sequence entry:', e)
            sys.exit(1)
    else:
        print('No sqlite_sequence entry to delete for', table_name)

    # Show final state
    try:
        cur.execute("SELECT name, seq FROM sqlite_sequence WHERE name=%s", [table_name])
        print('sqlite_sequence entry after:', cur.fetchall())
    except Exception:
        print('sqlite_sequence table absent or inaccessible after operation')

if __name__ == '__main__':
    main()
