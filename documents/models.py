# documents/models.py (corrected and enhanced: Document va Order duplikatsiyasini to'g'irlash, Order uchun Signature qo'shish, QR kod uchun field)
from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings
import qrcode
from io import BytesIO
from django.core.files import File


# kerakmas
# class DocumentType(models.Model):
#     DOCUMENT_TYPES = (
#         ('internal', 'I/CH - Ichki hujjat'),
#         ('external', 'SH/T - Shartnoma/Tashqi hujjat'),
#     )
    
#     name = models.CharField(max_length=50, choices=DOCUMENT_TYPES, verbose_name='Hujjat turi')
#     branch = models.ForeignKey('users.Branch', on_delete=models.CASCADE, related_name='document_types')
#     description = models.TextField(verbose_name='Izoh', blank=True)
    
#     class Meta:
#         verbose_name = 'Hujjat turi'
#         verbose_name_plural = 'Hujjat turlari'
#         unique_together = ('name', 'branch')
    
#     def __str__(self):
#         return f"{self.get_name_display()} - {self.branch.name}"

class AdditionalDocumentTemplate(models.Model):
    name = models.CharField(max_length=255, verbose_name="Hujjat nomi")
    branch = models.ForeignKey(
        'users.Branch',
        on_delete=models.CASCADE,
        related_name='doc_templates',
        null=True,
        blank=True,
        verbose_name="Filial (Ixtiyoriy)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Faol")

    class Meta:
        verbose_name = "Qo'shimcha hujjat shabloni"
        verbose_name_plural = "Qo'shimcha hujjat shablonlari"
        ordering = ['name']

    def __str__(self):
        return self.name


class AdditionalDocument(models.Model):
    name = models.CharField(max_length=255, verbose_name="Hujjat nomi")
    file = models.FileField(upload_to='additional_docs/%Y/%m/', max_length=500, null=True, blank=True, verbose_name="Fayl")
    branch = models.ForeignKey(
        'users.Branch',
        on_delete=models.CASCADE,
        related_name='additional_documents',
        null=True,
        blank=True,
        verbose_name="Filial"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Imzolash uchun yangi maydonlar
    signer = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='additional_docs_to_sign',
        verbose_name="Imzolovchi xodim"
    )
    is_signed = models.BooleanField(default=False, verbose_name="Imzolandi")
    signed_at = models.DateTimeField(null=True, blank=True, verbose_name="Imzolangan vaqt")
    qr_code = models.ImageField(upload_to='additional_docs/qr/%Y/%m/', max_length=500, null=True, blank=True, verbose_name="QR kod")
    stamped_file = models.FileField(upload_to='additional_docs/stamped/%Y/%m/', max_length=500, null=True, blank=True, verbose_name="Pechatli PDF")
    
    class Meta:
        verbose_name = "Qo'shimcha hujjat"
        verbose_name_plural = "Qo'shimcha hujjatlar"
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Qoralama'),
        ('pending', 'Imzolash kutilmoqda'),
        ('partial', 'Qisman imzolangan'),
        ('completed', 'To‘liq imzolangan'),
        ('rejected', 'Rad etilgan'),
        ('cancelled', 'Bekor qilingan'),
    )

    SIGNATURE_TYPES = (
        ('sequential', 'Ketma-ket'),
        ('parallel', 'Parallel'),
    )
    
    DOCUMENT_TYPES = (
        ('internal', 'Buyruq I/CH - Ichki hujjat'),
        ('external', 'Buyruq SH/T - Shartnoma/Tashqi hujjat'),
        ('application', 'Ariza'),
    )

    title = models.CharField(max_length=255, verbose_name="Buyruq nomi/sarlavhasi")
    number = models.CharField(
        max_length=50,
        verbose_name="Buyruq raqami",
        help_text="Masalan: 01-2025, BR-145/26 va h.k."
    )
    
    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_orders',
        verbose_name="Yaratgan xodim"
    )
    
    branch = models.ForeignKey(
        'users.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name="Filial"
    )

    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES,
        default='internal',
        verbose_name="Turi"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Holati"
    )
    
    
    file = models.FileField(
        upload_to='orders/files/%Y/%m/',
        max_length=500,
        null=True,
        blank=True,
        verbose_name="Ilova qilingan fayl (PDF va boshq.)"
    )
    
    from django.utils import timezone
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Yaratilgan vaqti")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="O‘zgartirilgan vaqti")
    
    deadline = models.DateField(
        null=True,
        blank=True,
        verbose_name="Imzolash muddati"
    )

    signature_type = models.CharField(max_length=20, choices=SIGNATURE_TYPES, default='sequential')

    # Yangi maydonlar: Direktor tasdig'i va umumiy QR kod
    director_approved = models.BooleanField(default=False, verbose_name="Direktor tasdiqladi")
    director_approved_at = models.DateTimeField(null=True, blank=True, verbose_name="Direktor tasdiqlagan vaqt")
    final_qr_code = models.ImageField(upload_to='orders/final_qr/%Y/%m/', max_length=500, null=True, blank=True, verbose_name="Umumiy QR kod")
    stamped_file = models.FileField(upload_to='orders/stamped/%Y/%m/', max_length=500, null=True, blank=True, verbose_name="Pechatli PDF")

    additional_docs = models.ManyToManyField(
        'AdditionalDocument', 
        blank=True, 
        related_name='orders', 
        verbose_name="Qo'shimcha hujjatlar"
    )

    class Meta:
        verbose_name = "Buyruq"
        verbose_name_plural = "Buyruqlar"
        ordering = ['-created_at']
        unique_together = ('number', 'branch', 'document_type')
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"{self.number} - {self.title}"

    def update_status(self):
        signatures = self.signatures.all()
        total_signatures = signatures.count()
        signed_count = signatures.filter(signed=True).count()
        
        if total_signatures == 0:
            self.status = 'pending'
        elif signed_count == 0:
            self.status = 'pending'
        elif signed_count == total_signatures:
            # Barcha imzolar to'plangan — direktor tasdiqlaganmi yoki yo'qmi, baribir "completed"
            self.status = 'completed'
        elif signed_count > 0:
            self.status = 'partial'
        else:
            self.status = 'pending'
        
        self.save()

    def is_fully_signed(self):
        """Barcha OrderSignature imzolari yig'ilganmi?"""
        total_signatures = self.signatures.count()
        signed_count = self.signatures.filter(signed=True).count()
        return total_signatures > 0 and signed_count == total_signatures

    def get_pending_signers(self):
        signed_users = self.signatures.filter(signed=True).values_list('user__id', flat=True)
        return self.signers.exclude(user__id__in=signed_users)

    @property
    def signatures_signed_count(self):
        return self.signatures.filter(signed=True).count()

    @property
    def signatures_total_count(self):
        return self.signatures.count()

class OrderSigner(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='signers',
        verbose_name="Buyruq"
    )
    
    user = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='orders_to_sign',
        verbose_name="Imzolovchi"
    )
    
    order_number = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Imzolash tartib raqami",
        help_text="1 - birinchi imzolashi kerak, 2 - ikkinchi va h.k."
    )
    
    required = models.BooleanField(
        default=True,
        verbose_name="Majburiy imzo"
    )
    
    # comment = models.CharField(
    #     max_length=255,
    #     blank=True,
    #     verbose_name="Izoh / lavozim"
    # )

    class Meta:
        verbose_name = "Imzolovchi"
        verbose_name_plural = "Imzolovchilar"
        unique_together = [['order', 'user']]
        ordering = ['order_number']

    def __str__(self):
        return f"{self.order.number} → {self.user.get_full_name()}"

class OrderSignature(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='signatures')
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='order_signatures')
    order_number = models.PositiveIntegerField(verbose_name='Imzo tartibi')
    signature_image = models.ImageField(upload_to='order_signatures/%Y/%m/%d/', max_length=500, null=True, blank=True)
    qr_code = models.ImageField(upload_to='qr_codes/%Y/%m/%d/', max_length=500, null=True, blank=True)
    signed = models.BooleanField(default=False, verbose_name='Imzolandi')
    signed_at = models.DateTimeField(null=True, blank=True, verbose_name='Imzolangan vaqt')
    # comment = models.TextField(blank=True, verbose_name='Izoh')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Buyruq imzo'
        verbose_name_plural = 'Buyruq imzolar'
        unique_together = ('order', 'user')
        ordering = ['order_number']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.order.title}"
    
    def save(self, *args, **kwargs):
        if self.signed and not self.qr_code:
            # QR kod generatsiya
            data = f"Familya: {self.user.last_name}\nIsm: {self.user.first_name}\nOtasining ismi: {self.user.middle_name if hasattr(self.user, 'middle_name') else ''}\nImzolangan vaqt: {self.signed_at}\nBuyruq raqami: {self.order.number}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            self.qr_code.save(f"qr_{self.pk}.png", File(buffer), save=False)
        
        super().save(*args, **kwargs)
        self.order.update_status()

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('signature_request', 'Imzo so\'rovi'),
        ('document_signed', 'Hujjat imzolandi'),
        ('status_changed', 'Holat o\'zgardi'),
    )
    
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Bildirishnoma'
        verbose_name_plural = 'Bildirishnomalar'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.message[:50]}"