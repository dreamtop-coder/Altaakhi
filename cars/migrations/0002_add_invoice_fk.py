# Generated split migration to add Invoice FK after invoices initial migration
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('cars', '0001_initial'),
        ('invoices', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='maintenancerecord',
            name='invoice',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='maintenance_records', to='invoices.invoice', verbose_name='رقم الفاتورة'),
        ),
    ]
