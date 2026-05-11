p='static/js/line-items.ui.js'
s=open(p,'r',encoding='utf8').read()
stack=[]
line=1
i=0
n=len(s)
state='normal' # normal, sq, dq, bt, linec, blockc
while i<n:
    ch=s[i]
    # track line
    if ch=='\n':
        line+=1
    if state=='normal':
        if ch=="'": state='sq'; i+=1; continue
        if ch=='"': state='dq'; i+=1; continue
        if ch=='`': state='bt'; i+=1; continue
        if ch=='/' and i+1<n and s[i+1]=='/': state='linec'; i+=2; continue
        if ch=='/' and i+1<n and s[i+1]=='*': state='blockc'; i+=2; continue
        if ch=='(':
            stack.append((line,i))
        elif ch==')':
            if stack: stack.pop()
            else:
                print('Unmatched closing ) at line', line)
        i+=1
        continue
    elif state=='sq':
        if ch=='\\': i+=2; continue
        if ch=="'": state='normal'; i+=1; continue
        i+=1; continue
    elif state=='dq':
        if ch=='\\': i+=2; continue
        if ch=='"': state='normal'; i+=1; continue
        i+=1; continue
    elif state=='bt':
        if ch=='\\': i+=2; continue
        if ch=='`': state='normal'; i+=1; continue
        i+=1; continue
    elif state=='linec':
        if ch=='\n': state='normal'; i+=1; continue
        i+=1; continue
    elif state=='blockc':
        if ch=='*' and i+1<n and s[i+1]=='/': state='normal'; i+=2; continue
        i+=1; continue

# done
print('stack leftover count:', len(stack))
if stack:
    print('Last unmatched open paren at line', stack[-1][0], 'index', stack[-1][1])
    # print a small context
    ln=stack[-1][0]
    L = s.splitlines()
    start=max(1, ln-6)
    end=min(len(L), ln+6)
    print('\nContext:')
    for idx in range(start,end+1):
        print(str(idx).rjust(4), L[idx-1])
else:
    print('No unmatched opens found after stripping strings/comments')
