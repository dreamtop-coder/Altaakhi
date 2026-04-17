import os
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
cur.execute('''CREATE TABLE IF NOT EXISTS clients_client (
    id integer PRIMARY KEY AUTOINCREMENT,
    first_name varchar(100) NOT NULL,
    last_name varchar(100),
    phone_number varchar(20) NOT NULL,
    email varchar(254),
    address varchar(255),
    customer_id varchar(30) NOT NULL UNIQUE,
    status varchar(10) NOT NULL,
    notes text,
    communication_preference varchar(10) NOT NULL,
    birth_date date,
    created_by_id integer,
    created_at datetime,
    updated_at datetime NOT NULL
)
''')
# ensure migration record
cur.execute("SELECT COUNT(1) FROM django_migrations WHERE app='clients' AND name='0001_initial'")
if cur.fetchone()[0]==0:
    import datetime
    applied=datetime.datetime(2026,3,8,23,20,40)
    cur.execute("INSERT INTO django_migrations(app,name,applied) VALUES (?,?,?)", ('clients','0001_initial', applied.isoformat()))
    print('created table and inserted migration record')
else:
    print('migration record already present')
