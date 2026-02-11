from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0005_part_is_stock_item"),
    ]

    operations = [
        migrations.CreateModel(
            name="Purchase",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("invoice_number", models.CharField(blank=True, max_length=50, null=True)),
                ("date", models.DateField()),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("is_return", models.BooleanField(default=False)),
                ("notes", models.TextField(blank=True, null=True)),
                (
                    "supplier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="purchases",
                        to="inventory.supplier",
                    ),
                ),
            ],
        ),
    ]
