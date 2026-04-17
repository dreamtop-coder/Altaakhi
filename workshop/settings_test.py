from .settings import *
import os

# Ensure we use a separate test DB file
DATABASES = DATABASES.copy()
DATABASES['default'] = DATABASES['default'].copy()
DATABASES['default']['NAME'] = os.path.join(BASE_DIR, 'db_test.sqlite3')
