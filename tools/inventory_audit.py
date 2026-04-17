from django.db.models import Sum
from inventory.models import Part
from bills.models import BillLine

print('id\tname\tcurrent_qty\texpected_sum')
mismatches = []
for p in Part.objects.all():
    # first try BillLines linked via part_id
    s = None
    for field in ('quantity','qty'):
        try:
            s = BillLine.objects.filter(part_id=p.id).aggregate(total=Sum(field))['total']
            break
        except Exception:
            s = None
    if s is None:
        s = 0
    # additionally sum BillLines that have no part link but description matches the part name
    try:
        desc_sum = 0
        for field in ('quantity','qty'):
            try:
                ds = BillLine.objects.filter(part_id__isnull=True, description__icontains=p.name).aggregate(total=Sum(field))['total']
                if ds:
                    desc_sum += float(ds)
            except Exception:
                continue
        s = float(s or 0) + float(desc_sum or 0)
    except Exception:
        s = float(s or 0)
    try:
        cur = float(p.quantity or 0)
    except Exception:
        cur = 0.0
    try:
        exp = float(s or 0)
    except Exception:
        exp = 0.0
    if round(cur,3) != round(exp,3):
        mismatches.append((p.id, p.name, cur, exp))
        print(f"{p.id}\t{p.name}\t{cur}\t{exp}")

print('\nMISMATCH_COUNT=', len(mismatches))

# Optionally write the report to a file
try:
    with open('inventory_audit_report.txt', 'w', encoding='utf-8') as f:
        f.write('id\tname\tcurrent_qty\texpected_sum\n')
        for row in mismatches:
            f.write(f"{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}\n")
        f.write(f"\nMISMATCH_COUNT= {len(mismatches)}\n")
    print('\nReport written to inventory_audit_report.txt')
except Exception as e:
    print('Failed to write report:', e)
