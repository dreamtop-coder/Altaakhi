import requests
import sys

BILL_ID = 7
URL = f'http://127.0.0.1:8000/bills/edit/{BILL_ID}/'
try:
    r = requests.get(URL, timeout=10)
except Exception as e:
    print('ERROR_FETCH', str(e))
    sys.exit(2)
if r.status_code != 200:
    print('HTTP', r.status_code)
    sys.exit(3)
html = r.text
if 'option value="expense" selected' in html or "option value='expense' selected" in html:
    print('TYPE_DISPLAYED: expense selected')
    sys.exit(0)
# fallback: check for <select class="item-account-type" and a nearby option
if 'item-account-type' in html and 'value="expense"' in html:
    # not strictly selected, but present
    print('TYPE_PRESENT_BUT_NOT_SELECTED')
    sys.exit(1)
print('TYPE_NOT_FOUND')
sys.exit(4)
