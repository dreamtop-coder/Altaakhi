import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState

loader = MigrationLoader(connection)
print('loader attrs:', [a for a in dir(loader) if not a.startswith('_')])
cur = connection.cursor()
cur.execute("SELECT app,name FROM django_migrations ORDER BY id")
rows = cur.fetchall()
state = ProjectState()
# Determine where migration objects are stored on loader
migrations_map = None
for attr in ('disk_migrations', 'migrations', 'graph', 'migration_plan'):
    if hasattr(loader, attr):
        print('has', attr)

# Prefer loader.disk_migrations if present
if hasattr(loader, 'disk_migrations'):
    migrations_map = loader.disk_migrations
elif hasattr(loader, 'migrations'):
    migrations_map = loader.migrations
elif hasattr(loader, 'graph') and hasattr(loader.graph, 'nodes'):
    migrations_map = {k: v.migration for k, v in loader.graph.nodes.items()}

for app, name in rows:
    print('MUTATING:', app, name)
    mig = None
    if migrations_map:
        try:
            mig = migrations_map.get((app, name))
        except Exception:
            # some loader mappings are different shapes
            pass
    if not mig:
        print('  (no migration file found for this applied migration; skipping)')
        continue
    try:
        mig.mutate_state(state)
    except Exception:
        import traceback
        traceback.print_exc()
        print('FAILED on', app, name)
        break
print('STATE BUILD COMPLETE')
