from django import forms
from django.contrib.auth import get_user_model
from website.models import Blog, ContactInquiry, AppointmentInquiry, BlogSubscription, BlogComment
from users.models import User

User = get_user_model()


class ContactInquiryForm(forms.ModelForm):
    """Form for contact inquiries"""
    
    class Meta:
        model = ContactInquiry
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Phone'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Your Message'
            }),
        }


class AppointmentInquiryForm(forms.ModelForm):
    """Form for appointment inquiries"""
    
    class Meta:
        model = AppointmentInquiry
        fields = [
            'name', 'email', 'phone', 'department', 
            'preferred_doctor', 'message', 'preferred_date', 'health_records'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Email'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Phone'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'preferred_doctor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Your Message'
            }),
            'preferred_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'health_records': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter doctors only
        self.fields['preferred_doctor'].queryset = User.objects.filter(role='DOCTOR').order_by('first_name', 'last_name')
        self.fields['preferred_doctor'].empty_label = "Any Available Doctor"
