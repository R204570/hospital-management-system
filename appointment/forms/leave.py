from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from appointment.models import Appointment, DoctorAvailability, DoctorLeaveRequest
from patient.models import Patient

User = get_user_model()


class DoctorLeaveRequestForm(forms.ModelForm):
    """Form for doctor leave requests"""
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now().date()
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now().date()
    )
    
    class Meta:
        model = DoctorLeaveRequest
        fields = ['start_date', 'end_date', 'start_time', 'end_time', 'reason']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Please provide a detailed reason for your leave request'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
        
        # If we have an instance, set the doctor right away
        if self.instance and not self.instance.pk and self.doctor:
            self.instance.doctor = self.doctor
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Start date must be before or equal to end date")
        
        # Special case: both start and end time are 00:00, treat as full day leave
        if start_time and end_time and start_time == end_time and start_time.hour == 0 and start_time.minute == 0:
            # This is a full-day leave request, so set end_time to 23:59
            import datetime
            cleaned_data['end_time'] = datetime.time(23, 59)
            return cleaned_data
            
        # Normal validation for other time ranges    
        if start_time and end_time and start_time >= end_time:
            raise ValidationError("Start time must be before end time")
            
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Make sure the doctor is set
        if self.doctor:
            instance.doctor = self.doctor
            
        instance.status = DoctorLeaveRequest.PENDING
        
        if commit:
            instance.save()
            
        return instance


class LeaveRequestReviewForm(forms.ModelForm):
    """Form for admin to review leave requests"""
    class Meta:
        model = DoctorLeaveRequest
        fields = ['status', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'admin_notes': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Optional notes about this decision'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.admin_user = kwargs.pop('admin_user', None)
        super().__init__(*args, **kwargs)
        
        # Limit status choices for admin review
        self.fields['status'].choices = [
            (DoctorLeaveRequest.APPROVED, 'Approve Leave Request'),
            (DoctorLeaveRequest.REJECTED, 'Reject Leave Request'),
        ]
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.reviewed_by = self.admin_user
        instance.reviewed_at = timezone.now()
        
        if commit:
            instance.save()
            
        return instance
