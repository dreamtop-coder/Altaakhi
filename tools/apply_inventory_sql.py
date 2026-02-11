import sqlite3
import os
DB='db.sqlite3'
sqls = [
    '''CREATE TABLE IF NOT EXISTS "inventory_purchase" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "invoice_number" varchar(50) NULL, "date" date NOT NULL, "amount" decimal NOT NULL, "is_return" bool NOT NULL, "notes" text NULL, "supplier_id" integer NOT NULL REFERENCES "inventory_supplier" ("id") DEFERRABLE INITIALLY DEFERRED);''',
    '''CREATE TABLE IF NOT EXISTS "inventory_part" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(100) NOT NULL, "quantity" integer NOT NULL CHECK ("quantity" >= 0), "low_stock_alert" integer NOT NULL CHECK ("low_stock_alert" >= 0), "department_id" integer NULL REFERENCES "services_department" ("id") DEFERRABLE INITIALLY DEFERRED, "supplier_id" integer NULL REFERENCES "inventory_supplier" ("id") DEFERRABLE INITIALLY DEFERRED);''',
    '''CREATE INDEX IF NOT EXISTS "inventory_purchase_supplier_id_d098a335" ON "inventory_purchase" ("supplier_id");''',
    '''CREATE INDEX IF NOT EXISTS "inventory_part_department_id_03348451" ON "inventory_part" ("department_id");''',
    '''CREATE INDEX IF NOT EXISTS "inventory_part_supplier_id_8e4da424" ON "inventory_part" ("supplier_id");''',
]

print('db_exists=', os.path.exists(DB))
conn=sqlite3.connect(DB)
cur=conn.cursor()
for s in sqls:
    try:
        cur.execute(s)
        print('executed')
    except Exception as e:
        print('error executing:', e)
conn.commit()
conn.close()
print('done')
