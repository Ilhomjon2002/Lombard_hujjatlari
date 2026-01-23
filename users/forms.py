from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import CustomUser, Branch


class CustomUserForm(UserCreationForm):
    branch = forms.ModelMultipleChoiceField(
        queryset=Branch.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Filial(lar)",
        help_text="Bir yoki bir nechta filial tanlang (Ctrl yoki Shift bilan)"
    )

    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'role', 'branch', 'profile_image', 'signature_image'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'login (masalan: john_doe)'}),
            'email': forms.EmailInput(attrs={'placeholder': 'email@company.uz'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Ism'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Familiya'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'profile_image': forms.FileInput(),
            'signature_image': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'placeholder': 'Parol kiriting (min 8 belgi)'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Parolni takrorlang'})

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and CustomUser.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Bu login allaqachon band.")
        return username.lower().strip()

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Bu email allaqachon ro‘yxatdan o‘tgan.")
        return email.lower().strip() if email else email


class UserUpdateForm(forms.ModelForm):
    branch = forms.ModelMultipleChoiceField(
        queryset=Branch.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Filial(lar)"
    )

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email',
            'role', 'branch', 'is_active',
            'profile_image', 'signature_image'
        ]
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(),
            'profile_image': forms.FileInput(),
            'signature_image': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['branch'].initial = self.instance.branch.all()


class UserPasswordResetForm(forms.Form):
    new_password1 = forms.CharField(
        label="Yangi parol",
        min_length=8,
        widget=forms.PasswordInput(attrs={'placeholder': 'Yangi parol'}),
    )
    new_password2 = forms.CharField(
        label="Tasdiqlash",
        widget=forms.PasswordInput(attrs={'placeholder': 'Yangi parolni takrorlang'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password1")
        p2 = cleaned_data.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Parollar mos kelmadi.")
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'profile_image', 'signature_image']
        widgets = {
            'profile_image': forms.FileInput(attrs={'accept': 'image/*'}),
            'signature_image': forms.FileInput(attrs={'accept': 'image/*'}),
        }



class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'placeholder': 'Joriy parol'})
        self.fields['new_password1'].widget.attrs.update({'placeholder': 'Yangi parol'})
        self.fields['new_password2'].widget.attrs.update({'placeholder': 'Yangi parolni takrorlang'})