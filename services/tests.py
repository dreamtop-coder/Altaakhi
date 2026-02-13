from django.test import TestCase
from django.core.management import call_command
from services.models import Service
from inventory.models import Part
import csv
import tempfile
import os


class MapServicesToItemsServiceTests(TestCase):
	def test_basic_matching_and_csv_output(self):
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

	def test_create_placeholders_non_dry_run(self):
		# No parts exist that match this service name, so placeholder should be created
		service_name = "Unique Service XYZ"
		Service.objects.create(name=service_name, default_price=0, department=None)

		tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
		tmp.close()
		try:
			# run command in non-dry-run mode and auto-confirm with --yes
			call_command("map_services_to_items", "--no-dry-run", "--create-placeholders", "--yes", "--output", tmp.name)
			with open(tmp.name, newline="", encoding="utf-8") as f:
				reader = csv.DictReader(f)
				rows = list(reader)

			# Placeholder Part should now exist
			self.assertTrue(Part.objects.filter(name=service_name).exists())
			# CSV should contain a created_placeholder entry for our service
			self.assertTrue(any(r.get('service_name') == service_name and r.get('match_type') == 'created_placeholder' for r in rows))
		finally:
			os.unlink(tmp.name)
