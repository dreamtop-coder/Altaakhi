import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
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

migrations_map = loader.disk_migrations if hasattr(loader, 'disk_migrations') else loader.migrations

for app, name in rows:
    print('\nMUTATING:', app, name)
    mig = migrations_map.get((app, name))
    if not mig:
        print('  (no migration file found for this applied migration; skipping)')
        continue
    ops = getattr(mig, 'operations', None)
    print('  migration object:', type(mig), 'ops count:', len(ops) if ops is not None else 'None')
    if ops:
        for i,op in enumerate(ops):
            print('   op', i, type(op), getattr(op, 'name', repr(op)))
    try:
        mig.mutate_state(state)
    except Exception:
        import traceback
        traceback.print_exc()
        print('FAILED on', app, name)
        break
    # debug: check whether contenttype model was added
    if app == 'contenttypes' and name == '0001_initial':
        print('  state has contenttype?', ('contenttypes', 'contenttype') in state.models)
print('\nSTATE BUILD COMPLETE')
