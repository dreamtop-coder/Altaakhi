from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)


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
    return [b for b in bookings if getattr(b, "car_id", None) == car_id]
