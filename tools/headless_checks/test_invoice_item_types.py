# Headless check: verify item-type hidden inputs and totals on edit invoice
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE','workshop.settings')
import django
django.setup()
from django.test import Client
from playwright.sync_api import sync_playwright
from django.contrib.auth import get_user_model

User = get_user_model()

def run():
    user, _ = User.objects.get_or_create(username='headless_test', defaults={'email':'headless@example.com'})
    user.set_password('P@ssw0rd123')
    user.is_staff = True
    user.is_superuser = True
    user.save()

    client = Client()
    logged_in = client.login(username='headless_test', password='P@ssw0rd123')
    if not logged_in:
        print('ERROR: could not log in headless_test')
        sys.exit(2)
    sid = client.cookies.get('sessionid')

    url = 'http://127.0.0.1:8000/invoices/edit/11/'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        if sid:
            page.context.add_cookies([{'name':'sessionid','value':sid.value,'domain':'127.0.0.1','path':'/'}])
        page.goto(url, wait_until='networkidle')
        page.wait_for_timeout(700)
        # ensure clientside serialization + recompute
        page.evaluate('() => { try{ if(window.serializeMaintenanceItems) window.serializeMaintenanceItems(); if(window.recomputeTotals) window.recomputeTotals(); }catch(e){} }')
        types = page.evaluate("() => Array.from(document.querySelectorAll('.item-type-hidden')).map(e=>e.value)")
        svc = page.query_selector('#services-sub-total') and page.eval_on_selector('#services-sub-total','el=>el.textContent')
        parts = page.query_selector('#sub-total') and page.eval_on_selector('#sub-total','el=>el.textContent')
        grand = page.query_selector('#grand-total') and page.eval_on_selector('#grand-total','el=>el.textContent')
        print('types:', types)
        print('services-sub-total:', svc)
        print('parts-sub-total:', parts)
        print('grand-total:', grand)

        ok = True
        if not all(t in ('service','inventory') for t in types):
            print('FAIL: unexpected type values')
            ok = False
        if not svc or float(svc) <= 0:
            print('FAIL: services subtotal non-positive or missing')
            ok = False
        if not parts:
            print('FAIL: parts subtotal missing')
            ok = False
        # basic sanity: grand == services + parts
        try:
            s = float(svc or 0)
            p = float(parts or 0)
            g = float(grand or 0)
            if abs((s + p) - g) > 0.001:
                print('FAIL: totals mismatch (svc+parts != grand)')
                ok = False
        except Exception as e:
            print('FAIL: could not parse totals', e)
            ok = False

        browser.close()

    if ok:
        print('TEST PASS')
        return 0
    else:
        print('TEST FAIL')
        return 1

if __name__ == '__main__':
    sys.exit(run())
