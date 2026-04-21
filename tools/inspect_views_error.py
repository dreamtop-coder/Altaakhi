p='invoices/views.py'
with open(p, 'r', encoding='utf-8') as f:
    lines = f.readlines()
start = 1718
end = 1738
for i in range(start-1, end):
    try:
        print(f'{i+1:5d}: {lines[i].rstrip()}')
    except IndexError:
        print(f'{i+1:5d}: <no line>')
