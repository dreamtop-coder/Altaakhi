from pathlib import Path
p=Path('static/js/line-items.ui.js')
if not p.exists():
    print('file not found', p)
    raise SystemExit(1)
s=p.read_text()
lines=s.splitlines()
for i,l in enumerate(lines, start=1):
    if 'catch' in l:
        prev=''
        for j in range(max(0,i-4), i-1):
            prev += f"{j+1}: {lines[j]}\n"
        print(f"{i}: {l.strip()}")
        print('prev lines:\n'+prev)
        print('---')
