from django.db import migrations


def forwards_func(apps, schema_editor):
    Invoice = apps.get_model('invoices', 'Invoice')
    # Convert existing 'stock' values to 'sales'
    try:
        Invoice.objects.filter(type='stock').update(type='sales')
    except Exception:
        pass


def reverse_func(apps, schema_editor):
    Invoice = apps.get_model('invoices', 'Invoice')
    # On reverse migration, convert 'sales' back to 'stock'
    try:
        Invoice.objects.filter(type='sales').update(type='stock')
    except Exception:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0003_add_invoice_type'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
