from django.contrib.auth import get_user_model
U = get_user_model()
u = U.objects.filter(username='mahdi').first()
if not u:
    print('USER_NOT_FOUND')
else:
    u.is_staff = True
    u.is_superuser = True
    u.save()
    print('UPDATED', u.username, u.is_staff, u.is_superuser)
