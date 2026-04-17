import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE','workshop.settings')
import django
django.setup()
from django.db import connection
cur=connection.cursor()
# Create department table
cur.execute('''CREATE TABLE IF NOT EXISTS services_department (
    id integer PRIMARY KEY AUTOINCREMENT,
    name varchar(50) NOT NULL
)
''')
# Create service table
cur.execute('''CREATE TABLE IF NOT EXISTS services_service (
    id integer PRIMARY KEY AUTOINCREMENT,
    name varchar(100) NOT NULL,
    description text,
    default_price decimal(10,2) NOT NULL,
    status varchar(10) NOT NULL,
    notes text,
    created_at datetime,
    updated_at datetime,
    car_id integer,
    department_id integer
)
''')
# Insert migration record if missing
cur.execute("SELECT COUNT(1) FROM django_migrations WHERE app='services' AND name='0001_initial'")
if cur.fetchone()[0]==0:
    import datetime
    applied=datetime.datetime(2026,3,8,23,28,0)
    ts = applied.isoformat()
    cur.execute(f"INSERT INTO django_migrations(app,name,applied) VALUES ('services','0001_initial','{ts}')")
    print('created services tables and inserted migration record')
else:
    print('services migration already present')
