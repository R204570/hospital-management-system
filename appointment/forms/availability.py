from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from appointment.models import Appointment, DoctorAvailability, DoctorLeaveRequest
from patient.models import Patient

User = get_user_model()


class DoctorAvailabilityForm(forms.ModelForm):
    """Form for doctor availability"""
    class Meta:
        model = DoctorAvailability
        fields = ['day_of_week', 'start_time', 'end_time']
        widgets = {
            'day_of_week': forms.Select(attrs={'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.doctor = self.doctor
        
        if commit:
            instance.save()
            
        return instance
