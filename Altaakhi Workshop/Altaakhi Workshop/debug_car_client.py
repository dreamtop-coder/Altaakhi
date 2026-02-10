from clients.models import Client
from cars.models import Car

# فحص وجود سيارة برقم لوحة معين وعميلها
plate = input("أدخل رقم اللوحة: ")
car = Car.objects.filter(plate_number=plate).first()
if car:
    print(f"السيارة موجودة: {car.plate_number}، معرف العميل: {car.client_id}")
    client = car.client
    print(f"بيانات العميل: {client.id}, {client.first_name} {client.last_name}")
else:
    print("لا توجد سيارة بهذا الرقم.")

# فحص جميع السيارات والعملاء المرتبطين
for car in Car.objects.all():
    print(f"Car: {car.plate_number}, Client: {car.client_id}")
for client in Client.objects.all():
    print(f"Client: {client.id}, Cars: {client.cars.count()}")
