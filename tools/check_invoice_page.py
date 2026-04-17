from django.test import Client

c = Client()
ok = c.login(username='test', password='testpass')
print('login=', ok)
r = c.get('/invoices/add/')
print('status=', r.status_code)
txt = r.content.decode('utf-8')
keys = ['id="customer-search"','id="customer-search-btn"','id="add-row"','id="items-body"','id="items_json"']
for k in keys:
    print(k+':', 'FOUND' if k in txt else 'MISSING')
# optionally write the HTML to a file for inspection
open('tools/_invoice_add_page.html','w', encoding='utf-8').write(txt)
print('wrote tools/_invoice_add_page.html')
