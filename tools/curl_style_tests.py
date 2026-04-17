#!/usr/bin/env python3
"""
cURL-style HTTP tests for inventory validation
Usage: python tools/curl_style_tests.py
"""
import json
import sys
try:
    import requests
except Exception:
    print('requests library is required. Install with: pip install requests')
    sys.exit(1)

BASE = 'http://127.0.0.1:8000'
# Use the test client/part created earlier (adjust IDs if different)
TEST_CLIENT_ID = 47
# Use part by name (one of TEST parts) to match description-based lookup
PART_NAME = 'TEST_PART_A'

print('Posting to /cars/maintenance/add/ with qty > stock (999)')
print('GET the form to obtain CSRF token and session cookie')
url = BASE + '/maintenance/add/'
items = [{'description': PART_NAME, 'qty': 999, 'rate': 9.99, 'discount': 0, 'amount': 9.99}]
session = requests.Session()
try:
    g = session.get(url, timeout=10)
    print('GET status:', g.status_code)
    csrftoken = session.cookies.get('csrftoken', '')
    if not csrftoken:
        # Try to extract token from HTML
        import re
        m = re.search(r"name='csrfmiddlewaretoken' value='([^']+)'", g.text)
        csrftoken = m.group(1) if m else ''
    payload = {
        'selected_client_id': str(TEST_CLIENT_ID),
        'items_json': json.dumps(items),
        'action': 'save_send',
        'invoice_number': '',
        'csrfmiddlewaretoken': csrftoken,
    }
    headers = {'Referer': url, 'X-CSRFToken': csrftoken}
    r = session.post(url, data=payload, headers=headers, timeout=10)
    print('POST status code:', r.status_code)
    print('Response headers:', dict(r.headers))
    print('Response body (truncated 1000 chars):')
    print(r.text[:1000])
except Exception as e:
    print('Request failed:', e)

print('\nDone')
