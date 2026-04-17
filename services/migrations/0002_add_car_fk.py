from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("services", "0001_initial"),
        ("cars", "0004_alter_maintenancerecord_created_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="car",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='services', to='cars.car'),
        ),
    ]
