import urllib.request
urls=[
    'http://127.0.0.1:8000/bills/',
    'http://127.0.0.1:8000/suppliers/',
    'http://127.0.0.1:8000/vendors/payments/'
]
for u in urls:
    try:
        r=urllib.request.urlopen(u, timeout=5)
        html=r.read().decode('utf-8', errors='ignore')
        print(u, 'status', r.getcode(), 'components.css found?', 'components.css' in html)
        if 'components.css' not in html and 'vendors/payments' in u:
            idx = html.find('components.css')
            print('--- excerpt around components.css (not found) ---')
            print(html[:2000])
            # list all referenced CSS files in the page
            import re
            css_links = re.findall(r'href=["\']([^"\']+\.css)["\']', html)
            print('CSS links found on page:', css_links)
    except Exception as e:
        print(u, 'ERROR', e)
