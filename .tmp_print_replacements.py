import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
import django
django.setup()
from django.db import connection
from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(connection)
print('replacements keys sample (first 20):')
for k,v in list(loader.replacements.items())[:20]:
    print(k,'->',v)
print('\nreplacements count:', len(loader.replacements))
