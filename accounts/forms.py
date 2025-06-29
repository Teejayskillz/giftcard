# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.forms.widgets import PasswordInput
from .models import User, Currency 
from .models import AutoConversionRule

class AutoConversionRuleForm(forms.ModelForm):
    class Meta:
        model = AutoConversionRule
        fields = ['from_currency', 'to_currency', 'threshold', 'rate_override', 'is_active']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['from_currency'].queryset = Currency.objects.filter(
                pk__in=self.user.wallets.values_list('currency__pk', flat=True)
            ).distinct()


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Email Address",
        help_text="Required. Enter a valid email address.",
        max_length=254
    )
    first_name = forms.CharField(max_length=30, required=True, label="First Name")
    last_name = forms.CharField(max_length=30, required=True, label="Last Name")
    phone = forms.CharField(max_length=20, required=True, label="Phone Number")

    class Meta(UserCreationForm.Meta):
        model = User
        # *** CRITICAL FIX: DO NOT include 'password' or 'password2' here. ***
        # UserCreationForm already provides them.
        fields = ('username', 'email', 'first_name', 'last_name', 'phone')
        # You can keep the widgets for styling
        widgets = {
            'password': PasswordInput(attrs={'class': 'form-control'}),
            'password2': PasswordInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("A user with that phone number already exists.")
        return phone


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone',)