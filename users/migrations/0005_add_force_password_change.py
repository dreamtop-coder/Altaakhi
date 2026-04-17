from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_alter_auditlog_action'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='force_password_change',
            field=models.BooleanField(default=False),
        ),
    ]
