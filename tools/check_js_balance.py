#!/usr/bin/env python3
import sys
from pathlib import Path

def check_file(path):
    s = Path(path).read_text(encoding='utf-8')
    pairs = {'(':')','[':']','{':'}'}
    stack = []
    state = 'NORMAL'
    L = len(s)
    for i,ch in enumerate(s):
        if state=='NORMAL':
            if ch=="'": state='S'; continue
            if ch=='"': state='D'; continue
            if ch=='`': state='T'; continue
            if ch=='/':
                if i+1<L and s[i+1]=='/': state='LC'; continue
                if i+1<L and s[i+1]=='*': state='BC'; continue
            if ch in '([{': stack.append((ch,i))
            elif ch in ')]}':
                if not stack:
                    print(f'Unmatched closing {ch} at line {s.count("\n",0,i)+1}')
                    return 2
                last,li = stack[-1]
                exp = pairs[last]
                if ch==exp:
                    stack.pop()
                else:
                    print(f'Mismatched closing {ch} expected {exp} at line {s.count("\n",0,i)+1}')
                    print(f'Top of stack: {last} opened at line {s.count("\n",0,li)+1}')
                    start = max(0, li-120)
                    end = min(L, i+120)
                    ctx = s[start:end]
                    print('\n--- context around opener/mismatch ---\n')
                    print(ctx)
                    return 3
        elif state=='S':
            if ch=='\\':
                # skip escaped char
                continue
            if ch=="'": state='NORMAL'
        elif state=='D':
            if ch=='\\':
                continue
            if ch=='"': state='NORMAL'
        elif state=='T':
            if ch=='\\':
                continue
            if ch=='`': state='NORMAL'
        elif state=='LC':
            if ch=='\n': state='NORMAL'
        elif state=='BC':
            if ch=='*' and i+1<L and s[i+1]=='/': state='NORMAL';

    if stack:
        print('Unclosed opens:', len(stack))
        for ch,idx in stack[-10:]:
            print(f"{ch} at line {s.count('\n',0,idx)+1}")
        return 4
    print('All balanced')
    return 0

if __name__=='__main__':
    if len(sys.argv)>1:
        path = sys.argv[1]
    else:
        path = 'static/js/line-items.ui.js'
    rc = check_file(path)
    sys.exit(rc)

