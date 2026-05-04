import os
import sys
from pathlib import Path
import re
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','workshop.settings')
import django
django.setup()
from django.test import Client
from django.conf import settings
from invoices.models import Invoice
from cars.maintenance_models import MaintenanceRecord


def find_rows(html):
    parts = html.split('<tr')
    rows = []
    for p in parts[1:]:
        rows.append('<tr' + p)
    return rows


def extract_data_type(row_html):
    m = re.search(r'data-type="([^"]*)"', row_html)
    return m.group(1) if m else ''


def extract_invoice_number_from_row(row_html):
    # Try to find invoice number by simple heuristic: digits/letters sequence inside a td
    # Prefer explicit anchor text if present
    m = re.search(r'>([A-Za-z0-9\-_/ ]{1,60})<', row_html)
    if m:
        return m.group(1).strip()
    return None


def main():
    c = Client()
    try:
        if 'testserver' not in settings.ALLOWED_HOSTS:
            settings.ALLOWED_HOSTS += ['testserver']
    except Exception:
        pass
    # login
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.filter(is_staff=True).first()
    if not user:
        user = User.objects.create(username='e2e_filter_user', is_staff=True)
        user.set_password('e2e')
        user.save()
    c.force_login(user)

    ok = True
    # Fetch invoices page
    resp = c.get('/invoices/')
    html = resp.content.decode('utf-8')
    rows = find_rows(html)
    invoices = Invoice.objects.all()
    missing = []
    mismatched = []
    for inv in invoices:
        found = False
        for r in rows:
            if inv.invoice_number in r:
                found = True
                dt = extract_data_type(r).lower()
                expected = (inv.type or '').lower()
                # normalize legacy 'sale' to 'sales'
                if expected == 'sale': expected = 'sales'
                if dt != expected:
                    mismatched.append((inv.invoice_number, expected, dt))
                break
        if not found:
            missing.append(inv.invoice_number)

    print('Invoices page: total_invoices=%d, missing_rows=%d, mismatches=%d' % (invoices.count(), len(missing), len(mismatched)))
    if missing:
        print('Missing invoice rows (not found on page):', missing[:10])
    if mismatched:
        print('Mismatched data-type entries (invoice, expected, actual):')
        for m in mismatched[:20]:
            print(' ', m)

    if missing or mismatched:
        ok = False

    # Fetch maintenance page and ensure shown invoices are maintenance-related
    resp2 = c.get('/maintenance/')
    html2 = resp2.content.decode('utf-8')
    rows2 = find_rows(html2)
    maint_invoice_numbers = set()
    for r in rows2:
        # look for invoice number patterns like INV123 or numeric tokens
        # try to match known invoice numbers from DB
        for inv in invoices:
            if inv.invoice_number in r:
                maint_invoice_numbers.add(inv.invoice_number)

    bad_ones = []
    for inv_num in maint_invoice_numbers:
        inv = Invoice.objects.filter(invoice_number=inv_num).first()
        if not inv:
            bad_ones.append((inv_num, 'not_found'))
            continue
        if (inv.type or '').lower() == 'sales' or (inv.type or '').lower() == 'sale':
            bad_ones.append((inv_num, 'is_sales'))
            continue
        # ensure there's at least one MaintenanceRecord linked to this invoice
        if not MaintenanceRecord.objects.filter(invoice=inv).exists():
            bad_ones.append((inv_num, 'no_maintenance_record'))

    print('Maintenance page: invoices_found=%d, bad_count=%d' % (len(maint_invoice_numbers), len(bad_ones)))
    if bad_ones:
        for b in bad_ones[:20]:
            print(' ', b)
        ok = False

    if not ok:
        print('E2E FILTER TEST: FAILED')
        sys.exit(2)
    print('E2E FILTER TEST: PASSED')


if __name__ == '__main__':
    main()
