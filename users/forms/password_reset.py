from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm, PasswordChangeForm
from django.utils.translation import gettext_lazy as _
from users.models import User


class ForgotPasswordForm(forms.Form):
    """Form for initiating password reset"""
    employee_id = forms.CharField(
        label="License Number or Employee ID",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your license number or employee ID'})
    )
    email = forms.EmailField(
        label="Registered Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your registered email'})
    )


class OTPVerificationForm(forms.Form):
    """Form for OTP verification"""
    otp = forms.CharField(
        label="OTP Code",
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter 6-digit OTP',
            'autocomplete': 'off'
        })
    )


class SetNewPasswordForm(forms.Form):
    """Form for setting new password after OTP verification"""
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'})
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data
