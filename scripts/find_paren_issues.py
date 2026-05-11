# Quick diagnostic: list lines containing 'catch' and scan cumulative paren balance
import sys
p='static/js/line-items.ui.js'
s=open(p,'r',encoding='utf8').read()
lines=s.splitlines()
print('TOTAL LINES:', len(lines))
print('\nLines containing "catch":')
for i,l in enumerate(lines):
    if 'catch' in l:
        print(i+1, l.strip())

# cumulative parenthesis balance (counts all occurrences naively)
openp=0
maxdiff=0
maxline=0
first_positive=None
for i,l in enumerate(lines):
    openp += l.count('(') - l.count(')')
    if first_positive is None and openp>0:
        first_positive = i+1
    if openp>maxdiff:
        maxdiff=openp; maxline=i+1

print('\nCumulative paren result:')
print('final_diff', openp)
print('max_diff', maxdiff, 'at line', maxline)
if first_positive:
    print('first line where diff became >0:', first_positive)

# print context around the suspicious line(s)
ctx_start = max(1, maxline-6)
ctx_end = min(len(lines), maxline+6)
print('\nContext around max_diff line ({}–{}):'.format(ctx_start, ctx_end))
for i in range(ctx_start, ctx_end+1):
    print(str(i).rjust(6), lines[i-1])

# final counts
print('\nFinal raw counts: backticks:', s.count('`'), '({})'.format(s.count('`')%2 and 'odd' or 'even'))
print('{:', s.count('{'), '}:', s.count('}'))
print('(:', s.count('('), '):', s.count(')'))
