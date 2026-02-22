import os
import sys
import django
from collections import Counter

# setup Django
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'workshop.settings')
django.setup()

from django.utils import timezone
from clients.models import Client
from cars.models import Car
from services.models import Service
from cars.maintenance_models import MaintenanceRecord
from invoices.models import Invoice, Payment
from cars.views import derive_car_status
import requests
from django.contrib.auth import get_user_model

BASE = 'http://127.0.0.1:8000'

def contains_plate_in_endpoint(plate, url):
    try:
        r = requests.get(url, timeout=5)
        return plate in r.text
    except Exception as e:
        print('HTTP error for', url, e)
        return False


def ensure_client_and_car():
    cid = f'SMOKE-{int(timezone.now().timestamp())%100000}'
    client, _ = Client.objects.get_or_create(first_name='SMOKE', last_name='TEST', defaults={'phone_number': '0000000000', 'customer_id': cid})
    plate = f'SMOKE{int(timezone.now().timestamp())%100000}'
    car, created = Car.objects.get_or_create(plate_number=plate, defaults={'client': client, 'status': 'waiting'})
    if not car.client_id:
        car.client = client
        car.status = 'waiting'
        car.save()
    return client, car


def print_status(step, car):
    derived = derive_car_status(car)
    print(f"[{step}] Car {car.plate_number} DB status={car.status} derived={derived}")


def main():
    client, car = ensure_client_and_car()
    print('Created test client/car:', client.id, car.plate_number)

    urls = {
        'waiting': BASE + '/cars/ajax/filter/?status=waiting',
        'in_progress': BASE + '/cars/ajax/filter/?status=in_progress',
        'pending_payment': BASE + '/cars/ajax/filter/?status=pending_payment',
        'ready': BASE + '/cars/ajax/filter/?status=ready',
        'done': BASE + '/cars/ajax/filter/?status=done',
        'paid_waiting_collection': BASE + '/cars/ajax/filter/?status=paid_waiting_collection',
    }

    print_status('initial', car)
    print('AJAX waiting contains plate?', contains_plate_in_endpoint(car.plate_number, urls['waiting']))

    # Step: add maintenance record -> should move to in_progress
    from services.models import Department
    dept = Department.objects.first() or Department.objects.create(name='General')
    svc, _ = Service.objects.get_or_create(name='SMOKE SERVICE', defaults={'default_price': 100, 'department': dept})
    mr = MaintenanceRecord.objects.create(car=car, service=svc, price=120, notes='smoke test', created_at=timezone.now())
    # mimic add_maintenance view transition
    if car.status in ['waiting', 'active', '', None]:
        car.status = 'in_progress'
        car.save()
    print_status('after add maintenance', car)
    print('AJAX in_progress contains plate?', contains_plate_in_endpoint(car.plate_number, urls['in_progress']))

    # Step: finish maintenance -> set is_finished, ready_at, car -> pending_payment and create invoice if none unpaid
    mr.is_finished = True
    mr.ready_at = timezone.now()
    mr.save()
    # check if all maintenance finished
    if not car.maintenance_records.filter(is_finished=False).exists():
        car.status = 'pending_payment'
        car.save()
        # create invoice if no unpaid
        inv = car.invoices.filter(paid=False).first()
        if not inv:
            inv = Invoice.objects.create(invoice_number=f'INV-SMOKE-{car.id}-{int(timezone.now().timestamp())}', client=client, car=car, amount=mr.price, paid=False, created_at=timezone.now())
            mr.invoice = inv
            mr.save()
    print_status('after finish', car)
    print('AJAX pending_payment contains plate?', contains_plate_in_endpoint(car.plate_number, urls['pending_payment']))

    # Step: simulate payment
    inv = car.invoices.filter(paid=False).first()
    if inv:
        pay = Payment.objects.create(invoice=inv, amount=inv.amount, payment_date=timezone.now(), car=car, client=client, status='paid')
        inv.paid = True
        inv.save()
        # set DB status to paid_waiting_collection to mimic UI flow
        car.status = 'paid_waiting_collection'
        car.save()
    print_status('after payment', car)
    print('AJAX ready contains plate?', contains_plate_in_endpoint(car.plate_number, urls['ready']))
    print('AJAX paid_waiting_collection contains plate?', contains_plate_in_endpoint(car.plate_number, urls['paid_waiting_collection']))

    # Step: deliver/collect -> try hitting deliver endpoint with DEBUG test hook
    deliver_url = BASE + f'/cars/deliver/{car.id}/'
    # Ensure a staff user exists for login (so we can obtain CSRF-protected session)
    User = get_user_model()
    username = 'smoketest'
    password = 'smokepass'
    try:
        user, created = User.objects.get_or_create(username=username, defaults={'is_staff': True, 'is_active': True})
        if created:
            user.set_password(password)
            user.is_staff = True
            user.save()
        else:
            # ensure staff and set known password for test runs
            if not user.is_staff:
                user.is_staff = True
            try:
                user.set_password(password)
                user.save()
            except Exception:
                pass
    except Exception:
        user = None

    try:
        s = requests.Session()
        login_url = BASE + '/users/login/'
        # GET login page to populate CSRF cookie
        try:
            s.get(login_url, timeout=5)
        except Exception:
            pass
        csrf = s.cookies.get('csrftoken', '')
        headers = {'Referer': login_url, 'X-CSRFToken': csrf}
        # perform login
        try:
            s.post(login_url, data={'username': username, 'password': password}, headers=headers, timeout=5)
        except Exception:
            pass

        # Now post to deliver endpoint using authenticated session
        try:
            csrfd = s.cookies.get('csrftoken', '')
            hdr = {'Referer': deliver_url, 'X-CSRFToken': csrfd}
            r = s.post(deliver_url, data={'force_status': 'paid_waiting_collection'}, headers=hdr, timeout=5)
            print('Deliver POST', r.status_code)
            if r.text:
                print('Deliver response snippet:', r.text[:200])
            # if response indicates forbidden, fallback to DB update
            if r.status_code == 403:
                raise Exception('403 Forbidden')
        except Exception as e:
            print('Deliver POST failed, falling back to DB update:', e)
            for rec in car.maintenance_records.filter(delivery_date__isnull=True):
                rec.delivery_date = timezone.now()
                rec.save()
            car.status = 'done'
            car.save()
    except Exception as e:
        print('Session/login setup failed, falling back to DB update:', e)
        for rec in car.maintenance_records.filter(delivery_date__isnull=True):
            rec.delivery_date = timezone.now()
            rec.save()
        car.status = 'done'
        car.save()

    # report final status and AJAX visibility
    print_status('after collect', car)
    print('AJAX done contains plate?', contains_plate_in_endpoint(car.plate_number, urls['done']))
    print('AJAX paid_waiting_collection contains plate?', contains_plate_in_endpoint(car.plate_number, urls['paid_waiting_collection']))


if __name__ == '__main__':
    main()
