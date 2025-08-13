from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from .models import Appointment, DoctorAvailability, DoctorLeaveRequest
from patient.models import Patient

User = get_user_model()


class TimeSlotForm(forms.Form):
    """Form for selecting timeslots"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'id_slot-date'}),
        initial=timezone.now().date()
    )
    doctor = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.DOCTOR),
        empty_label="Select a doctor",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_slot-doctor'})
    )
    time_slot = forms.CharField(required=False, widget=forms.HiddenInput())


class AppointmentForm(forms.ModelForm):
    """Form for creating and editing appointments"""
    doctor = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.DOCTOR),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'doctor-select'})
    )
    patient = forms.ModelChoiceField(
        queryset=Patient.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'patient-select'})
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'date-select'}),
        initial=timezone.now().date()
    )
    is_emergency = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'is-emergency'}),
        help_text="Check this box for emergency appointments (available 24/7)"
    )
    
    class Meta:
        model = Appointment
        fields = [
            'patient', 'doctor', 'date', 'start_time', 'end_time',
            'appointment_type', 'reason', 'is_emergency'
        ]
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'readonly': 'readonly'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'readonly': 'readonly'}),
            'appointment_type': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        print(f"AppointmentForm initialized with user: {self.user}")
        
        # If this is a doctor user, restrict to only their own profile
        if self.user and self.user.is_doctor:
            self.fields['doctor'].initial = self.user
            self.fields['doctor'].widget.attrs['disabled'] = 'disabled'
            self.fields['doctor'].required = False
            print(f"Setting doctor field to current user (doctor): {self.user}")
        
        # Make sure all fields are properly initialized
        for field_name, field in self.fields.items():
            if not 'class' in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
                
        # Debug initial values
        if args and args[0]:  # POST data
            print("Form submitted with POST data")
            for field_name in self.fields:
                if field_name in args[0]:
                    print(f"- {field_name}: {args[0].get(field_name)}")
            
            # Time slot handling
            if 'time_slot' in args[0]:
                print(f"- time_slot: {args[0].get('time_slot')}")
        
        elif kwargs.get('initial'):
            print("Form initialized with data:")
            for field_name, value in kwargs['initial'].items():
                print(f"- {field_name}: {value}")
    
    def clean(self):
        cleaned_data = super().clean()
        print("Cleaning form data...")
        
        # If doctor field was disabled (for doctor users), use the logged-in user
        if self.user and self.user.is_doctor:
            cleaned_data['doctor'] = self.user
            print(f"Setting doctor to current user: {self.user}")
        
        # Ensure start_time and end_time are set
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if not start_time or not end_time:
            print("Missing start_time or end_time, checking time_slot")
            # Try to get from time_slot field in POST data
            if self.data.get('time_slot'):
                try:
                    start, end = self.data.get('time_slot').split(',')
                    import datetime
                    cleaned_data['start_time'] = datetime.datetime.strptime(start, '%H:%M').time()
                    cleaned_data['end_time'] = datetime.datetime.strptime(end, '%H:%M').time()
                    print(f"Set times from time_slot: {start} - {end}")
                except (ValueError, IndexError) as e:
                    print(f"Error parsing time_slot: {e}")
        
        # Handle emergency flag
        is_emergency = cleaned_data.get('is_emergency', False)
        appointment_type = cleaned_data.get('appointment_type')
        
        if is_emergency and appointment_type != Appointment.EMERGENCY:
            print(f"Setting appointment type to EMERGENCY due to is_emergency flag")
            cleaned_data['appointment_type'] = Appointment.EMERGENCY
        
        # Final validation - make this more lenient
        missing_fields = []
        for field in ['patient', 'doctor', 'date', 'appointment_type', 'reason']:
            if field not in cleaned_data or not cleaned_data.get(field):
                missing_fields.append(field)
                print(f"Missing required field after cleaning: {field}")
                self.add_error(field, f"This field is required")
        
        # Handle time fields separately - be more permissive
        if ('start_time' not in cleaned_data or not cleaned_data.get('start_time')) and \
           ('end_time' not in cleaned_data or not cleaned_data.get('end_time')):
            # If both start and end time are missing, we need one of them
            if not self.data.get('time_slot'):
                print("Missing both time fields and no time_slot provided")
                self.add_error('start_time', "Please select a time slot")
                missing_fields.append('time')
        
        if missing_fields:
            print(f"Form has missing fields: {missing_fields}")
        else:
            print(f"All required fields present in cleaned data")
        
        print(f"Cleaned data: {cleaned_data}")
        return cleaned_data


class AppointmentStatusForm(forms.Form):
    """Form for updating appointment status"""
    status = forms.ChoiceField(
        choices=Appointment.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


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