from pathlib import Path
p=Path(r'c:\Users\Mahdi\Desktop\Altaakhi Workshop\static\js\items-table.v2.js')
s=p.read_text(encoding='utf-8')
stack=[]
pairs={')':'(',']':'[','}':'{'}
openers='([{'
closers=')]}'
for i,ch in enumerate(s,1):
    if ch in openers:
        stack.append((ch,i))
    elif ch in closers:
        if not stack:
            print('Extra closer',ch,'at',i)
            break
        top, pos = stack.pop()
        if pairs[ch]!=top:
            print('Mismatched', top, 'opened at', pos, 'but closed by', ch, 'at', i)
            break
else:
    if stack:
        print('Unclosed opener', stack[-1][0], 'at', stack[-1][1])
    else:
        print('All balanced')
