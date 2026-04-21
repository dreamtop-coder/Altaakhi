p='invoices/views.py'
s=open(p,'r',encoding='utf-8').read().splitlines()
line_no=1728
tries=0
excepts=0
for i,l in enumerate(s[:line_no]):
    if 'try:' in l:
        tries+=1
    if 'except ' in l or l.strip().startswith('except'):
        excepts+=1
print('up to line', line_no, 'tries=', tries, 'excepts=', excepts)
# print last 80 lines before error
for i,l in enumerate(s[line_no-80:line_no+10], start=line_no-79):
    print(f'{i:5d}: {l}')
