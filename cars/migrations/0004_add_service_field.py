from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("cars", "0002_maintenancepart"),
        ("services", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="maintenancerecord",
            name="service",
            field=models.ForeignKey(
                to="services.service",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
    ]
