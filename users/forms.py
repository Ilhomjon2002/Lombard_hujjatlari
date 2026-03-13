from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import CustomUser, Branch


class CustomUserForm(UserCreationForm):
    branch = forms.ModelMultipleChoiceField(
        queryset=Branch.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Branch(es)",
        help_text="Select one or more branches (use Ctrl or Shift to select multiple)"
    )

    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'middle_name',
            'profile_image', 'role', 'position'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'username (e.g., john_doe)'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'Ism'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Familiya'}),
            'middle_name': forms.TextInput(attrs={'placeholder': 'Otasining ismi'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'position': forms.TextInput(attrs={'placeholder': 'Masalan: Bosh hisobchi'}),
            'profile_image': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'placeholder': 'Password (minimum 8 characters)'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm Password'})

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and CustomUser.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username.lower().strip()

        return username.lower().strip()


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
            'first_name', 'last_name', 'middle_name',
            'profile_image', 'role', 'position', 'is_active', 'branch'
        ]
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(),
            'profile_image': forms.FileInput(),
            'position': forms.TextInput(attrs={'placeholder': 'Masalan: Bosh hisobchi'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['branch'].initial = self.instance.branch.all()

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # M2M ni branch orqali saqlash
            if 'branch' in self.cleaned_data:
                user.branch.set(self.cleaned_data['branch'])
        return user

class UserPasswordResetForm(forms.Form):
    new_password1 = forms.CharField(
        label="New Password",
        min_length=8,
        widget=forms.PasswordInput(attrs={'placeholder': 'New Password'}),
    )
    new_password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm New Password'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password1")
        p2 = cleaned_data.get("new_password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'profile_image']
        widgets = {
            'profile_image': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'placeholder': 'Current Password'})
        self.fields['new_password1'].widget.attrs.update({'placeholder': 'New Password'})
        self.fields['new_password2'].widget.attrs.update({'placeholder': 'Confirm New Password'})
