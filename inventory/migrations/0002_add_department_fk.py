from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_squashed_0007_part_track_purchases_part_track_sales'),
        ('services', '0002_add_parts_and_car'),
    ]

    operations = [
        migrations.AddField(
            model_name='part',
            name='department',
            field=models.ForeignKey(
                to='services.department',
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                related_name='parts',
            ),
        ),
    ]
