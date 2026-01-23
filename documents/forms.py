from django import forms
from django.utils.translation import gettext_lazy as _
from .models import DocumentType, Order, OrderSigner, OrderSignature
from users.models import Branch, CustomUser


class DocumentTypeForm(forms.ModelForm):
    class Meta:
        model = DocumentType
        fields = ['name', 'branch', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class EditSignatureForm(forms.ModelForm):
    class Meta:
        model = OrderSignature
        fields = ['signed', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

class OrderCreateForm(forms.ModelForm):
    """
    Buyruq yaratish uchun asosiy forma
    (create_document view uchun moslashtirilgan)
    """
    employees = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.filter(role='employee'),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Imzo qo‘yuvchi xodimlar",
        help_text="Imzo qo‘yishi kerak bo‘lgan xodimlarni tanlang"
    )

    class Meta:
        model = Order
        fields = [
            'number', 'title', 'branch', 'content',
            'file', 'signature_type', 'deadline'
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 6}),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'signature_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agar filial tanlangan bo'lsa, faqat shu filialdagi xodimlarni ko'rsatish mumkin
        # lekin bu view da dinamik qilinishi kerak (JS yoki ajax bilan)


class OrderSignerForm(forms.ModelForm):
    class Meta:
        model = OrderSigner
        fields = ['user', 'order_number', 'required', 'comment']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.TextInput(),
        }


class OrderSignatureAdminForm(forms.ModelForm):
    """
    Admin panelda imzo ma'lumotlarini tahrirlash uchun (masalan signed_at ni o'zgartirish)
    """
    class Meta:
        model = OrderSignature
        fields = ['signed', 'signed_at', 'comment']
        widgets = {
            'signed_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }


class OrderFilterForm(forms.Form):
    """
    Buyruqlarni filtr qilish uchun (masalan dashboard yoki ro'yxat sahifasida)
    """
    status = forms.ChoiceField(
        choices=[('', '—— Barchasi ——')] + list(Order.STATUS_CHOICES),
        required=False,
        label="Holati"
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        required=False,
        empty_label="—— Barcha filiallar ——",
        label="Filial"
    )
    search = forms.CharField(
        required=False,
        label="Qidiruv",
        widget=forms.TextInput(attrs={'placeholder': 'Raqam yoki sarlavha bo‘yicha qidirish...'})
    )