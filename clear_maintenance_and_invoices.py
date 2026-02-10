import os
import django


def main():
	# إعداد Django قبل استيراد نماذج المشروع
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "workshop.settings")
	django.setup()

	from cars.models import MaintenanceRecord
	from invoices.models import Invoice

	# حذف جميع سجلات الصيانة والفواتير (بيانات تجريبية فقط)
	MaintenanceRecord.objects.all().delete()
	Invoice.objects.all().delete()

	print("تم حذف جميع سجلات الصيانة والفواتير بنجاح.")


if __name__ == "__main__":
	main()
