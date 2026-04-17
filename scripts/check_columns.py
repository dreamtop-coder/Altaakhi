import sqlite3

def show_table_columns(db, table):
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info('%s')" % table)
        rows = cur.fetchall()
        if not rows:
            print(f"{table}: (no such table or no columns)")
        else:
            print(f"{table} columns:")
            for r in rows:
                # PRAGMA returns: cid, name, type, notnull, dflt_value, pk
                print('  ', r[1], r[2])
    except Exception as e:
        print(f"ERROR checking {table}:", e)
    finally:
        try:
            conn.close()
        except:
            pass

if __name__ == '__main__':
    db = 'db.sqlite3'
    for t in ('inventory_part','invoices_invoice'):
        show_table_columns(db, t)
