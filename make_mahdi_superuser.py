import os
import django


def main():
    # إعداد بيئة Django ثم استيراد نموذج المستخدم
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "workshop.settings")
    django.setup()

    from users.models import User

    username = "Mahdi"
    user = User.objects.filter(username=username).first()
    if user:
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print(f"تم إعطاء جميع الصلاحيات للمستخدم: {username}")
    else:
        print(f"المستخدم {username} غير موجود.")


if __name__ == "__main__":
    main()
