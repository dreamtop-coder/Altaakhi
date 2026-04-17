from django.test import Client

c = Client()
ok = c.login(username='test', password='testpass')
print('login=', ok)
# include HTTP_HOST to avoid DisallowedHost
r = c.get('/invoices/add/', HTTP_HOST='127.0.0.1')
print('status=', r.status_code)
txt = r.content.decode('utf-8')
keys = ['id="customer-search"','id="customer-search-btn"','id="add-row"','id="items-body"','id="items_json"']
for k in keys:
    print(k+':', 'FOUND' if k in txt else 'MISSING')
open('tools/_invoice_add_page2.html','w', encoding='utf-8').write(txt)
print('wrote tools/_invoice_add_page2.html')
