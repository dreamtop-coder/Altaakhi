from django.core.management.base import BaseCommand
from cars.models import Car
from invoices.models import Invoice, Payment

class Command(BaseCommand):
    help = 'Reset a car to pre-delivery/payment state (for testing/debug)'

    def add_arguments(self, parser):
        parser.add_argument('plate_number', type=str, help='Car plate number')
        parser.add_argument('--status', type=str, default='active', help='New status for the car (active/waiting)')

    def handle(self, *args, **options):
        plate_number = options['plate_number']
        new_status = options['status']
        try:
            car = Car.objects.get(plate_number=plate_number)
        except Car.DoesNotExist:
            self.stdout.write(self.style.ERROR('Car not found'))
            return
        # إعادة حالة السيارة
        car.status = new_status
        car.save()
        # إعادة الفاتورة إلى غير مدفوعة
        invoices = Invoice.objects.filter(car=car, paid=True)
        for invoice in invoices:
            invoice.paid = False
            invoice.save()
        # حذف جميع الدفعات المرتبطة بهذه السيارة
        Payment.objects.filter(car=car, status='paid').delete()
        self.stdout.write(self.style.SUCCESS(f'Reset car {plate_number} to status {new_status} and removed payments'))
