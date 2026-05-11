import re
s = open('templates/add_maintenance_record.html', encoding='utf8').read()
re_script = re.compile(r'<script(?:[^>]*)>([\s\S]*?)</script>', re.IGNORECASE)
all = re_script.findall(s)
content = all[7]
lines = content.splitlines()
depth=0
for i,l in enumerate(lines, start=1):
    # remove strings to avoid braces inside strings
    line = re.sub(r"'(?:\\.|[^'\\])*'", "'',", l)
    line = re.sub(r'\"(?:\\.|[^\\\"])*\"', '"",', line)
    # remove comments
    line = re.sub(r'//.*', '', line)
    # count
    opens = line.count('{')
    closes = line.count('}')
    depth += opens - closes
    print(f'{i:04} depth={depth:3} opens={opens} closes={closes} | {l}')
    if depth < 0:
        print('NEGATIVE DEPTH at line', i)
        break
print('final depth', depth)
