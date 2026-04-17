# Generated migration to add reminder_only and status fields
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0005_expensecategory_recurringexpense_expense'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='expense',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('posted', 'Posted')], default='posted', max_length=10),
        ),
        migrations.AlterField(
            model_name='recurringexpense',
            name='amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name='recurringexpense',
            name='reminder_only',
            field=models.BooleanField(default=False, help_text='If set, create a draft reminder expense instead of a posted expense'),
        ),
    ]
