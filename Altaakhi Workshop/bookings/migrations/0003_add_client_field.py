from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0001_initial"),
        ("bookings", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="client",
            field=models.ForeignKey(
                null=True,
                blank=True,
                to="clients.client",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="bookings",
            ),
        ),
    ]

