from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payment


@receiver(post_save, sender=Payment)
def update_car_status_on_payment(sender, instance, **kwargs):
    # إذا تم دفع الفاتورة بالكامل (status == 'paid')
    if instance.status == "paid":
        car = instance.car or (instance.invoice.car if instance.invoice else None)
        if car and car.status == "pending_payment":
            car.status = "sold"
            car.save()
