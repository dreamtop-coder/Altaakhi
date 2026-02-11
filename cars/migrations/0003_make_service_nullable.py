from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("cars", "0004_add_service_field"),
    ]

    operations = [
        migrations.AlterField(
            model_name="maintenancerecord",
            name="service",
            field=models.ForeignKey(
                to="services.service",
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                blank=True,
            ),
        ),
    ]
