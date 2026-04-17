
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)


@register.filter
def dict_get(dictionary, key):
    try:
        return dictionary.get(key, 0)
    except Exception:
        return 0

# فلتر: يعيد فقط الحجوزات المرتبطة بالسيارة المطلوبة
@register.filter
def dictfilterbycar(bookings, car_id):
    """
    usage: {{ bookings|dictfilterbycar:car.id }}
    يعيد فقط الحجوزات التي booking.car_id == car_id
    """
    try:
        car_id = int(car_id)
    except Exception:
        return []
    return [b for b in bookings if getattr(b, 'car_id', None) == car_id]


@register.filter
def status_en(status):
    """Return an English human-readable label for a car status code.

    Usage in templates: {{ car.status|status_en }}
    """
    try:
        mapping = {
            'waiting': 'Waiting',
            'in_progress': 'In Progress',
            'pending_payment': 'Pending Payment',
            'paid_waiting_collection': 'Paid - Waiting Collection',
            'done': 'Done',
            'active': 'Active',
            'ready': 'Ready',
            'sold': 'Sold',
        }
        return mapping.get(status, status or '')
    except Exception:
        return status or ''
