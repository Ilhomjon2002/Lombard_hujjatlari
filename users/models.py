# users/models.py (corrected and enhanced)
from django.db import models
from django.contrib.auth.models import AbstractUser

class Branch(models.Model):
    name = models.CharField(max_length=100, verbose_name='Filial nomi')
    # address = models.TextField(verbose_name='Manzil')
    # phone = models.CharField(max_length=20, verbose_name='Telefon')
    parent_branch = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='sub_branches', verbose_name='Yuqori filial')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Filial'
        verbose_name_plural = 'Filiallar'
    
    def __str__(self):
        return self.name

class Holiday(models.Model):
    date = models.DateField(unique=True, verbose_name='Dam olish kuni')
    description = models.CharField(max_length=255, blank=True, verbose_name='Izoh')
    branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.CASCADE, related_name='holidays', verbose_name='Filial (ixtiyoriy)')
    
    class Meta:
        verbose_name = 'Dam olish kuni'
        verbose_name_plural = 'Dam olish kunlari'
        ordering = ['date']
    
    def __str__(self):
        return f"{self.date} - {self.description or 'Dam olish kuni'}"

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('employee', 'Oddiy Ishchi'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    branch = models.ManyToManyField(
        Branch,
        related_name='employees',
        blank=True
    )
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    signature_image = models.ImageField(upload_to='signatures/', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.get_role_display()}"