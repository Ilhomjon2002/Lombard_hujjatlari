# Generated migration for physical fingerprint scanner support

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_fingerprint_credential'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScannerFingerprintTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_data', models.BinaryField(verbose_name='Encrypted Fingerprint Template')),
                ('quality_score', models.FloatField(default=0, verbose_name='Capture Quality (0-100)')),
                ('finger_position', models.CharField(
                    choices=[
                        ('right_thumb', 'Right Thumb'),
                        ('right_index', 'Right Index Finger'),
                        ('right_middle', 'Right Middle Finger'),
                        ('right_ring', 'Right Ring Finger'),
                        ('right_pinky', 'Right Pinky Finger'),
                        ('left_thumb', 'Left Thumb'),
                        ('left_index', 'Left Index Finger'),
                        ('left_middle', 'Left Middle Finger'),
                        ('left_ring', 'Left Ring Finger'),
                        ('left_pinky', 'Left Pinky Finger'),
                    ],
                    default='right_index',
                    max_length=20,
                    verbose_name='Finger Position'
                )),
                ('is_registered', models.BooleanField(default=False, verbose_name='Registered and Active')),
                ('registered_at', models.DateTimeField(auto_now_add=True, verbose_name='Registration Time')),
                ('last_verified', models.DateTimeField(blank=True, null=True, verbose_name='Last Verification')),
                ('verification_count', models.IntegerField(default=0, verbose_name='Successful Verifications')),
                ('algorithm', models.CharField(default='ZKTECO_MINEX', max_length=50, verbose_name='Algorithm')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='scanner_fingerprint', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Scanner Fingerprint Template',
                'verbose_name_plural': 'Scanner Fingerprint Templates',
            },
        ),
    ]
