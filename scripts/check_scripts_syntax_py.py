import re, sys
p = 'templates/add_maintenance_record.html'
s = open(p, encoding='utf8').read()
re_script = re.compile(r'<script(?:[^>]*)>([\s\S]*?)</script>', re.IGNORECASE)
all = re_script.findall(s)
print('Found', len(all), 'script tags')

for idx, content in enumerate(all, start=1):
    if not content.strip():
        print('skip empty script', idx)
        continue
    # simple stack parser for (), {}, [] and detect unclosed quotes
    stack = []
    quotes = None
    escaped = False
    problem = None
    for i,ch in enumerate(content):
        if quotes:
            if escaped:
                escaped = False
                continue
            if ch == '\\':
                escaped = True
                continue
            if ch == quotes:
                quotes = None
            continue
        else:
            if ch in ('"', "'"):
                quotes = ch
                continue
            if ch in '({[':
                stack.append((ch,i))
            elif ch in ')}]':
                if not stack:
                    problem = ('unmatched_closer', ch, i)
                    break
                open_ch, pos = stack.pop()
                pairs = { '(':')','{':'}','[':']' }
                if pairs.get(open_ch) != ch:
                    problem = ('mismatch', open_ch, ch, pos, i)
                    break
    if quotes and not problem:
        problem = ('unclosed_quote', quotes)
    if stack and not problem:
        problem = ('unclosed_open', stack[-1][0], stack[-1][1])
    if problem:
        print('\nBROKEN script index', idx, 'problem:', problem)
        lines = content.splitlines()
        # find line and context
        if problem[0] == 'unclosed_open' or problem[0] == 'mismatch' or problem[0]=='unmatched_closer':
            pos = problem[-1] if problem[0]=='mismatch' else problem[-1]
            # find line
            curr=0
            for li,l in enumerate(lines, start=1):
                curr += len(l)+1
                if curr > pos:
                    start = max(0, li-6)
                    for j in range(start, min(len(lines), li+6)):
                        print(f'{j+1}: {lines[j]}')
                    break
        else:
            for j in range(0, min(40, len(lines))):
                print(f'{j+1}: {lines[j]}')
        sys.exit(1)
    else:
        print('OK script', idx)
print('All scripts passed basic bracket/quote checks')
