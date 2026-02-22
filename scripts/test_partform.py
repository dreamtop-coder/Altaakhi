from inventory.forms import PartForm

def run():
    form = PartForm(data={'name':'T','code':'12','quantity':1,'purchase_price':'1.0','sale_price':'2.0'})
    print('is_valid (12):', form.is_valid())
    print('errors:', form.errors.as_json())
    form2 = PartForm(data={'name':'T','code':'0123','quantity':1,'purchase_price':'1.0','sale_price':'2.0'})
    print('is_valid (0123):', form2.is_valid())
    print('errors:', form2.errors.as_json())

if __name__=='__main__':
    run()
