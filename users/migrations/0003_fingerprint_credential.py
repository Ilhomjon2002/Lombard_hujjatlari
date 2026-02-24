# Generated migration for fingerprint authentication

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_remove_branch_address_remove_branch_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='fingerprint_enabled',
            field=models.BooleanField(default=False, verbose_name='Fingerprint Authentication Enabled'),
        ),
        migrations.CreateModel(
            name='FingerprintCredential',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('credential_id', models.TextField(unique=True, verbose_name='Credential ID')),
                ('credential_data', models.JSONField(verbose_name='Credential Public Key')),
                ('sign_count', models.IntegerField(default=0, verbose_name='Sign Count')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='fingerprint_credential', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Fingerprint Credential',
                'verbose_name_plural': 'Fingerprint Credentials',
            },
        ),
    ]
