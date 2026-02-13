from django.test import TestCase
from django.core.management import call_command
from services.models import Service
from inventory.models import Part
import csv
import tempfile
import os


class MapServicesToItemsTests(TestCase):
    def test_basic_matching_and_csv_output(self):
        # create a part and a service that should match
        p = Part.objects.create(name="Brake Pad", quantity=10, low_stock_alert=2)
        s = Service.objects.create(name="Brake Pad", default_price=5, department=None)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        tmp.close()
        try:
            call_command("map_services_to_items", "--output", tmp.name)
            with open(tmp.name, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertTrue(any(r['service_name'] == 'Brake Pad' and r['matched_part_name'] == 'Brake Pad' for r in rows))
        finally:
            os.unlink(tmp.name)
