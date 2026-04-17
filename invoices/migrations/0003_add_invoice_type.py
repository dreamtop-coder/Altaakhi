from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0002_alter_invoice_car_nullable'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='type',
            field=models.CharField(choices=[('stock', 'Stock Sale'), ('maintenance', 'Maintenance')], default='stock', max_length=20),
        ),
    ]
