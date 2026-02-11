from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0001_initial"),
        ("cars", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="car",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="services",
                to="cars.car",
            ),
        ),
    ]
