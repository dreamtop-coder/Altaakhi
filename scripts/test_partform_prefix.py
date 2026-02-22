from inventory.forms import PartForm

def run():
    examples = ['LB0001','MA0001','0001','003','A12','12A','ABC','']
    for ex in examples:
        form = PartForm(data={'name':'T','code':ex,'quantity':1,'purchase_price':'1.0','sale_price':'2.0'})
        print(ex, '-> valid:', form.is_valid(), 'errors:', form.errors.get('code'))

if __name__=='__main__':
    run()
