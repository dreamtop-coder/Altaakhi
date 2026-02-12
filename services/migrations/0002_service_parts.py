from django.db import migrations


class Migration(migrations.Migration):

    # No-op migration: replaced by squashed migration 0001_squashed_0003_add_car_fk
    # The squashed migration contains the Service model creation for new installs.
    # Keep dependency local to services to avoid circular references; the
    # actual parts M2M is created in services.0002_add_parts_and_car which
    # depends on `inventory.0004_part_purchase_price_part_sale_price`.
    dependencies = [
        ('services', '0001_initial'),
    ]

    operations = []
