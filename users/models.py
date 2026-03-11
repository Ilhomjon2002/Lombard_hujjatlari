# users/models.py (corrected and enhanced)
from django.db import models
from django.contrib.auth.models import AbstractUser
import json

class Branch(models.Model):
    name = models.CharField(max_length=100, verbose_name='Branch Name')
    address = models.TextField(verbose_name='Address')
    phone = models.CharField(max_length=20, verbose_name='Phone')
    # parent_branch = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='sub_branches', verbose_name='Parent Branch')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'
    
    def __str__(self):
        return self.name

# class Holiday(models.Model):
#     date = models.DateField(unique=True, verbose_name='Holiday Date')
#     description = models.CharField(max_length=255, blank=True, verbose_name='Description')
#     branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.CASCADE, related_name='holidays', verbose_name='Branch (Optional)')
    
#     class Meta:
#         verbose_name = 'Holiday'
#         verbose_name_plural = 'Holidays'
#         ordering = ['date']
    
#     def __str__(self):
#         return f"{self.date} - {self.description or 'Holiday'}"

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('employee', 'Ishchi'),
        ('director', 'Direktor'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    branch = models.ManyToManyField(
        Branch,
        related_name='employees',
        blank=True
    )
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    # signature_image = models.ImageField(upload_to='signatures/', null=True, blank=True)
    fingerprint_enabled = models.BooleanField(default=False, verbose_name='Fingerprint Authentication Enabled')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name='Otasining ismi')
    position = models.CharField(max_length=200, blank=True, verbose_name='Lavozim')
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.get_role_display()}"
    
    def get_full_name_with_middle(self):
        """Familiya Ism Otasining ismi"""
        parts = [self.last_name, self.first_name, self.middle_name]
        return ' '.join(p for p in parts if p)


class FingerprintCredential(models.Model):
    """Store WebAuthn credential data for fingerprint authentication"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='fingerprint_credential')
    credential_id = models.TextField(verbose_name='Credential ID', unique=True)
    credential_data = models.JSONField(verbose_name='Credential Public Key')
    sign_count = models.IntegerField(default=0, verbose_name='Sign Count')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Fingerprint Credential'
        verbose_name_plural = 'Fingerprint Credentials'
    
    def __str__(self):
        return f"Fingerprint for {self.user.get_full_name()}"


class ScannerFingerprintTemplate(models.Model):
    """Store physical fingerprint scanner template data"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='scanner_fingerprint')
    template_data = models.BinaryField(verbose_name='Encrypted Fingerprint Template')
    quality_score = models.FloatField(default=0, verbose_name='Capture Quality (0-100)')
    finger_position = models.CharField(
        max_length=20,
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
        verbose_name='Finger Position'
    )
    is_registered = models.BooleanField(default=False, verbose_name='Registered and Active')
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='Registration Time')
    last_verified = models.DateTimeField(null=True, blank=True, verbose_name='Last Verification')
    verification_count = models.IntegerField(default=0, verbose_name='Successful Verifications')
    algorithm = models.CharField(max_length=50, default='ZKTECO_MINEX', verbose_name='Algorithm')
    
    class Meta:
        verbose_name = 'Scanner Fingerprint Template'
        verbose_name_plural = 'Scanner Fingerprint Templates'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_finger_position_display()}"
