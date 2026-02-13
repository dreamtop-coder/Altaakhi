import os
from workshop import settings as base_settings

# Copy uppercase settings from base_settings
for name in dir(base_settings):
    if name.isupper():
        globals()[name] = getattr(base_settings, name)

# Ensure BASE_DIR is available
BASE_DIR = getattr(base_settings, 'BASE_DIR', os.path.dirname(os.path.abspath(__file__)))

# Override the default database path to a fresh SQLite file
DATABASES = dict(base_settings.DATABASES)
DATABASES['default'] = dict(DATABASES.get('default', {}))
DATABASES['default']['NAME'] = os.path.join(BASE_DIR, 'db.test.sqlite3')

# Optional: keep other settings unchanged
