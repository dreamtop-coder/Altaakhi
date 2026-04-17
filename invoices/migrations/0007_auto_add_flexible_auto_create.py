# Generated migration to add is_flexible and auto_create to RecurringExpense
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0006_auto_add_reminder_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='recurringexpense',
            name='is_flexible',
            field=models.BooleanField(default=False, help_text='If set, do not auto-create Expense on next_date'),
        ),
        migrations.AddField(
            model_name='recurringexpense',
            name='auto_create',
            field=models.BooleanField(default=True, help_text='If False, do not auto-create Expense even when not flexible'),
        ),
    ]
