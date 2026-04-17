import requests, json
BASE='http://127.0.0.1:8000'
login_url=BASE+'/users/login/'
invoice_id=92
edit_url=BASE+f'/invoices/edit/{invoice_id}/'
username='testman'
password='pw12345'

s=requests.Session()
# GET login to get CSRF
g=s.get(login_url)
csrf=s.cookies.get('csrftoken','')
print('Login GET', g.status_code, 'csrf', csrf)
headers={'Referer': login_url, 'X-CSRFToken': csrf}
# Post credentials
r=s.post(login_url, data={'username':username,'password':password,'csrfmiddlewaretoken':csrf}, headers=headers)
print('Login POST status', r.status_code)
# GET edit page to get csrf and ensure we can reach it
g2=s.get(edit_url)
print('Edit GET', g2.status_code)
csrf2=s.cookies.get('csrftoken','')
if not csrf2:
    import re
    m=re.search(r"name='csrfmiddlewaretoken' value='([^']+)'", g2.text)
    csrf2=m.group(1) if m else ''
print('edit csrf', csrf2)
headers2={'Referer': edit_url, 'X-CSRFToken': csrf2}
# prepare items_json increasing qty to 2 for TEST_PART_B
items=[{'description':'TEST_PART_B','qty':2,'rate':5.0,'disc':0}]
payload={'items_json': json.dumps(items),'amount':'','discount':'','created_at':'','csrfmiddlewaretoken':csrf2}
resp=s.post(edit_url, data=payload, headers=headers2)
print('Edit POST status', resp.status_code)
print('Contains shortage message?', 'الكمية غير متوفرة' in resp.text)
print('Response snippet:', resp.text[:1000])
