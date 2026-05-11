import re
s = open('templates/add_maintenance_record.html', encoding='utf8').read()
re_script = re.compile(r'<script(?:[^>]*)>([\s\S]*?)</script>', re.IGNORECASE)
all = re_script.findall(s)
content = all[7]  # index 7 -> 8th script
lines = content.splitlines()
for i,l in enumerate(lines[:260], start=1):
    print(f'{i:03}: {l}')
