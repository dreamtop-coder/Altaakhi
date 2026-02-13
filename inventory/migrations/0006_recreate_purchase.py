from django.db import migrations


class Migration(migrations.Migration):

    # This migration previously attempted to (re)create the Purchase model,
    # which caused the test DB creation to fail with "table already exists".
    # Make this migration a safe no-op to avoid duplicate table creation
    # during test database setup. The real schema already creates Purchase
    # in 0001_initial.py.

    dependencies = [
        ("inventory", "0005_part_is_stock_item"),
    ]

    operations = []
