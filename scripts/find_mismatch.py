import re, sys
p = 'templates/add_maintenance_record.html'
s = open(p, encoding='utf8').read()
re_script = re.compile(r'<script(?:[^>]*)>([\s\S]*?)</script>', re.IGNORECASE)
all = re_script.findall(s)
content = all[7]
print('script length', len(content))
stack=[]
quotes=None
escaped=False
for i,ch in enumerate(content):
    if quotes:
        if escaped:
            escaped=False
            continue
        if ch=='\\':
            escaped=True
            continue
        if ch==quotes:
            quotes=None
        continue
    else:
        if ch in ('"',"'"):
            quotes=ch; continue
        if ch in '({[':
            stack.append((ch,i))
        elif ch in ')}]':
            if not stack:
                ln = content[:i].count('\n')+1
                col = i - content.rfind('\n',0,i)
                print('UNMATCHED CLOSER', ch, 'at idx', i, 'line', ln, 'col', col)
                # print nearby lines
                lines = content.splitlines()
                start=max(0,ln-6)
                for j in range(start, min(len(lines), ln+6)):
                    print(f'{j+1:04}: {lines[j]}')
                sys.exit(0)
            open_ch,pos = stack.pop()
            pairs = {'(':')','{':'}','[':']'}
            if pairs.get(open_ch) != ch:
                ln = content[:i].count('\n')+1
                print('MISMATCH', open_ch, 'vs', ch, 'at idx', i, 'line', ln)
                sys.exit(0)
print('finished, stack size', len(stack))
if stack:
    oc,pos = stack[-1]
    ln = content[:pos].count('\n')+1
    col = pos - content.rfind('\n',0,pos)
    print('UNCLOSED OPEN', oc, 'at idx', pos, 'line', ln, 'col', col)
else:
    print('no problems')
