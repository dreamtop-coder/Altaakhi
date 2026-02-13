import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','workshop.settings')
import django
django.setup()
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState

loader = MigrationLoader(connection)
cur = connection.cursor()
cur.execute("SELECT app,name FROM django_migrations ORDER BY id")
rows = cur.fetchall()
state = ProjectState()
for app,name in rows:
    print('MUTATING:', app, name)
    mig = loader.migrations.get((app,name))
    if not mig:
        print('  (no migration file found for this applied migration; skipping)')
        continue
    try:
        mig.mutate_state(state)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('FAILED on', app, name)
        break
print('STATE BUILD COMPLETE')
