from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_part_purchase_price_part_sale_price'),
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='parts',
            field=models.ManyToManyField(blank=True, related_name='services', to='inventory.part'),
        ),
    ]
