import traceback
p='invoices/views.py'
source = open(p, 'r', encoding='utf-8').read()
try:
    compile(source, p, 'exec')
    print('compiled OK')
except Exception as e:
    traceback.print_exc()
    print('type:', type(e), 'args:', e.args)
