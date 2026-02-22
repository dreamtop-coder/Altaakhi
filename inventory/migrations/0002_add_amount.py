from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplier',
            name='amount',
            field=models.DecimalField(default=0, max_digits=12, decimal_places=2),
        ),
    ]
