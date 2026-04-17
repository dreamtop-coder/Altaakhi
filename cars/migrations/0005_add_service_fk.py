from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("cars", "0004_alter_maintenancerecord_created_at"),
        ("services", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="maintenancerecord",
            name="service",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="services.service"),
        ),
    ]
