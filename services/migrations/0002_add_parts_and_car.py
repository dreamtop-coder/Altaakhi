from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0001_squashed_0003_add_car_fk"),
        ("inventory", "0004_part_purchase_price_part_sale_price"),
        ("cars", "0004_maintenancerecord_maintenance_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="car",
            field=models.ForeignKey(
                to="cars.car",
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                blank=True,
                related_name="services",
            ),
        ),
        migrations.AddField(
            model_name="service",
            name="parts",
            field=models.ManyToManyField(blank=True, related_name="services", to="inventory.part"),
        ),
    ]
