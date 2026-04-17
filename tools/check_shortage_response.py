import requests, json
BASE='http://127.0.0.1:8000'
url=BASE+'/maintenance/add/'
session=requests.Session()
g=session.get(url)
csrftoken=session.cookies.get('csrftoken','')
items=[{'description':'TEST_PART_A','qty':999,'rate':9.99,'discount':0,'amount':9.99}]
payload={'selected_client_id':'47','items_json':json.dumps(items),'action':'save_send','invoice_number':'','csrfmiddlewaretoken':csrftoken}
headers={'Referer':url,'X-CSRFToken':csrftoken}
r=session.post(url,data=payload,headers=headers)
print('status',r.status_code)
print('contains shortage message?', 'الكمية غير متوفرة' in r.text)
print('response length', len(r.text))
