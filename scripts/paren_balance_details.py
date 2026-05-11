p='static/js/line-items.ui.js'
s=open(p,'r',encoding='utf8').read()
lines=s.splitlines()
openp=0
balances=[]
for i,l in enumerate(lines):
    openp += l.count('(') - l.count(')')
    balances.append(openp)

# print last 80 lines with balances
start=max(0, len(lines)-80)
print('Showing last {} lines with cumulative paren balance:'.format(len(lines)-start))
for i in range(start, len(lines)):
    print(str(i+1).rjust(6), str(balances[i]).rjust(4), lines[i])

# show first lines where balance==1 (if any)
first_one=None
for i,b in enumerate(balances):
    if b==1:
        first_one=i+1; break
print('\nfirst line with balance==1:', first_one)

# show lines where balance changes (for quick scan)
print('\nLines where balance changes:')
prev=balances[0]
print(1, prev, lines[0])
for i in range(1,len(lines)):
    if balances[i]!=prev:
        print(i+1, balances[i], lines[i])
        prev=balances[i]
