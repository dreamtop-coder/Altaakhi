from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("bookings", "0002_add_client_field"),
        ("clients", "0001_initial"),
    ]
    operations = []
