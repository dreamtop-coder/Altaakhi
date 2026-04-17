import requests, json, sys
from pprint import pprint
from decimal import Decimal

BASE = 'http://127.0.0.1:8000'
TEST_PART_ID = 35
TEST_USER = {'username': 'testman', 'password': 'pw12345'}

s = requests.Session()

def ensure_part(part_id):
    # run via manage.py shell to access Django ORM
    import os, subprocess
    cmd = ['.venv\Scripts\python.exe', 'manage.py', 'shell', '-c', \
           "from inventory.models import Part; p=Part.objects.filter(id=%d).first(); print(bool(p)); print(p.id if p else 'None'); print(p.name if p else '');" % part_id]
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = p.stdout.strip().splitlines()
    if len(out) >= 1 and out[0].strip() == 'True':
        pid = int(out[1].strip())
        name = out[2].strip()
        return pid, name
    # create a part
    cmd_create = ['.venv\\Scripts\\python.exe','manage.py','shell','-c',
                  "from inventory.models import Part; p=Part.objects.create(name='AUTO_TEST_PART_35', code='AUTO-35', quantity=0, track_stock=True); print(p.id); print(p.name)"]
    pc = subprocess.run(cmd_create, capture_output=True, text=True)
    lines = pc.stdout.strip().splitlines()
    if len(lines) >= 2:
        return int(lines[0].strip()), lines[1].strip()
    raise RuntimeError('Failed to ensure part')


def run_test_ajax_create_zero_stock(part_id, part_name):
    print('\n=== Test: ajax_create_invoice_zero_stock ===')
    # pre-state
    pre = get_part_state(part_id)
    print('Pre part quantity:', pre)
    # GET form to obtain CSRF
    url = BASE + '/invoices/add/'
    g = s.get(url)
    print('GET /invoices/add/ status', g.status_code)
    csrftoken = s.cookies.get('csrftoken', '')
    items = [{'part_id': part_id, 'description': part_name, 'qty': 5, 'price': 10}]
    payload = {'customer': '1', 'items_json': json.dumps(items), 'csrfmiddlewaretoken': csrftoken}
    headers = {'Referer': url, 'X-CSRFToken': csrftoken}
    r = s.post(url, data=payload, headers=headers)
    print('POST status', r.status_code)
    body = r.text
    has_msg = 'الكمية غير متوفرة' in body
    print('Contains shortage message?', has_msg)
    # post-state
    post = get_part_state(part_id)
    inv_count = count_invoices_with_item_description(part_name)
    item_count = count_invoiceitems_for_description(part_name)
    print('Post part quantity:', post)
    print('Invoice count with item desc:', inv_count)
    print('InvoiceItem count for desc:', item_count)
    return {'http_status': r.status_code, 'shortage_msg': has_msg, 'pre_qty': pre, 'post_qty': post, 'inv_count': inv_count, 'item_count': item_count}


def run_test_ajax_edit_exceed_stock(part_id, part_name):
    print('\n=== Test: ajax_edit_invoice_exceed_stock ===')
    # create invoice with qty=1 via ORM
    import subprocess
    cmd = ['.venv\\Scripts\\python.exe','manage.py','shell','-c',
           "from clients.models import Client; from invoices.models import Invoice, InvoiceItem; from django.utils import timezone; c=Client.objects.filter(customer_id__startswith='TEST-').first();\nif not c: c=Client.objects.create(first_name='TESTCLIENT', phone_number='00000', customer_id='TEST-C-AUTO');\ninv=Invoice.objects.create(invoice_number='INV-AJAX-TEST', client=c, amount=0, paid=False, created_at=timezone.now());\nInvoiceItem.objects.create(invoice=inv, description='%s', quantity=1, rate=10, discount=0, total=10); print(inv.id)" % part_name]
    p = subprocess.run(cmd, capture_output=True, text=True)
    inv_id = int(p.stdout.strip().splitlines()[-1])
    print('Created invoice id', inv_id)
    # set part quantity to 0
    subprocess.run(['.venv\\Scripts\\python.exe','manage.py','shell','-c',"from inventory.models import Part; p=Part.objects.get(id=%d); p.quantity=0; p.save(); print('set0')" % part_id], capture_output=True)
    pre = get_part_state(part_id)
    print('Pre part quantity:', pre)
    # login
    login_url = BASE + '/users/login/'
    g = s.get(login_url)
    csrf = s.cookies.get('csrftoken','')
    headers = {'Referer': login_url, 'X-CSRFToken': csrf}
    s.post(login_url, data={'username': TEST_USER['username'], 'password': TEST_USER['password'], 'csrfmiddlewaretoken': csrf}, headers=headers)
    # GET edit page to fetch csrf
    edit_url = BASE + f'/invoices/edit/{inv_id}/'
    ge = s.get(edit_url)
    csrf2 = s.cookies.get('csrftoken','')
    items = [{'part_id': part_id, 'description': part_name, 'qty': 10, 'price': 10}]
    payload = {'items_json': json.dumps(items), 'amount': '', 'discount': '', 'created_at': '', 'csrfmiddlewaretoken': csrf2}
    headers2 = {'Referer': edit_url, 'X-CSRFToken': csrf2}
    r = s.post(edit_url, data=payload, headers=headers2)
    print('Edit POST status', r.status_code)
    has_msg = 'الكمية غير متوفرة' in r.text
    print('Contains shortage message?', has_msg)
    post = get_part_state(part_id)
    items_after = count_invoiceitems_for_description(part_name)
    print('Post part quantity:', post)
    print('InvoiceItem count for desc:', items_after)
    return {'http_status': r.status_code, 'shortage_msg': has_msg, 'pre_qty': pre, 'post_qty': post, 'item_count': items_after, 'inv_id': inv_id}


def get_part_state(part_id):
    import subprocess
    cmd = ['.venv\\Scripts\\python.exe','manage.py','shell','-c',"from inventory.models import Part; p=Part.objects.filter(id=%d).values_list('quantity', flat=True).first(); print(p if p is not None else 'MISSING')" % part_id]
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = p.stdout.strip().splitlines()
    if out:
        v = out[-1].strip()
        if v == 'MISSING':
            return None
        try:
            return int(v)
        except Exception:
            try:
                return int(float(v))
            except Exception:
                return v
    return None


def count_invoices_with_item_description(desc):
    import subprocess
    cmd = ['.venv\\Scripts\\python.exe','manage.py','shell','-c',"from invoices.models import InvoiceItem; print(InvoiceItem.objects.filter(description__icontains='%s').count())" % desc]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return int(p.stdout.strip().splitlines()[-1])


def count_invoiceitems_for_description(desc):
    return count_invoices_with_item_description(desc)


if __name__ == '__main__':
    pid, pname = ensure_part(TEST_PART_ID)
    print('Using Part ID,Name:', pid, pname)
    r1 = run_test_ajax_create_zero_stock(pid, pname)
    r2 = run_test_ajax_edit_exceed_stock(pid, pname)
    print('\n=== Results Summary ===')
    pprint({'ajax_create': r1, 'ajax_edit': r2})
