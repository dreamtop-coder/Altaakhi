from django.contrib.auth import get_user_model
import secrets

U = get_user_model()
u = U.objects.filter(username='mahdi').first()
if not u:
    print('USER_NOT_FOUND')
else:
    tmp = secrets.token_urlsafe(10)
    u.set_password(tmp)
    u.save()
    print('PASSWORD_RESET', u.username, tmp)
