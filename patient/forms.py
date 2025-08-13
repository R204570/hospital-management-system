from django import forms
from .models import Patient, MedicalRecord, Room, Bed, Nurse, PatientAdmission, AdmissionRequest
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div
from datetime import datetime
from users.models import User


class PatientRegistrationForm(forms.ModelForm):
    """Form for registering new patients"""
    
    # Override date field to use a date picker widget
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    
    # Add profile picture field
    profile_picture = forms.ImageField(required=False)
    
    # Add medical_conditions field (instead of chronic_diseases)
    medical_conditions = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False
    )
    
    class Meta:
        model = Patient
        exclude = ['patient_id', 'registration_date', 'last_updated']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_relation': forms.TextInput(attrs={'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'chronic_diseases': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Map medical_conditions to chronic_diseases if the field exists
        if 'medical_conditions' in self.cleaned_data and hasattr(instance, 'chronic_diseases'):
            instance.chronic_diseases = self.cleaned_data['medical_conditions']
        
        if commit:
            instance.save()
        return instance


class PatientSearchForm(forms.Form):
    """Form for searching patients"""
    query = forms.CharField(
        label="Search Patients",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, ID, or phone number',
        })
    )


class MedicalRecordForm(forms.ModelForm):
    """Form for creating medical records"""
    class Meta:
        model = MedicalRecord
        fields = [
            'patient', 'doctor', 'blood_pressure', 'sugar_level', 
            'temperature', 'weight', 'symptoms', 'diagnosis', 
            'treatment_plan', 'prescription', 'blood_test_results', 
            'xray_image', 'precautions', 'diet', 'exercise', 
            'follow_up_date', 'notes'
        ]
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'doctor': forms.Select(attrs={'class': 'form-select'}),
            'blood_pressure': forms.TextInput(attrs={'class': 'form-control'}),
            'sugar_level': forms.TextInput(attrs={'class': 'form-control'}),
            'temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'symptoms': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'treatment_plan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'prescription': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'blood_test_results': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precautions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'diet': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'exercise': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'follow_up_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        # Extract the doctor parameter if provided
        doctor = kwargs.pop('doctor', None)
        
        super().__init__(*args, **kwargs)
        
        # Filter doctors to show only doctors
        self.fields['doctor'].queryset = User.objects.filter(role=User.DOCTOR)
        
        # If doctor is provided, set the initial value and make field read-only
        if doctor:
            self.fields['doctor'].initial = doctor
            self.fields['doctor'].disabled = True


class MedicalRecordFilterForm(forms.Form):
    """Form for filtering medical records"""
    doctor = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.DOCTOR),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class RoomForm(forms.ModelForm):
    """Form for creating/editing rooms"""
    class Meta:
        model = Room
        fields = ['floor', 'department', 'room_type', 'is_active']
        widgets = {
            'floor': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '6'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        floor = cleaned_data.get('floor')
        department = cleaned_data.get('department')
        room_type = cleaned_data.get('room_type')
        
        # Basic validation - ensure floor is within range
        if floor and (floor < 1 or floor > 6):
            self.add_error('floor', "Floor must be between 1 and 6")
        
        return cleaned_data


class BedForm(forms.ModelForm):
    """Form for creating/editing beds"""
    class Meta:
        model = Bed
        fields = ['room', 'bed_number', 'is_occupied', 'last_sanitized']
        widgets = {
            'room': forms.Select(attrs={'class': 'form-select'}),
            'bed_number': forms.TextInput(attrs={'class': 'form-control'}),
            'is_occupied': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'last_sanitized': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class NurseAssignmentForm(forms.ModelForm):
    """Form for nurse assignments"""
    class Meta:
        model = Nurse
        fields = ['nurse', 'assigned_floors', 'is_on_duty', 'max_patients', 'specialization']
        widgets = {
            'nurse': forms.Select(attrs={'class': 'form-select'}),
            'assigned_floors': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., [1, 2, 3]'}),
            'is_on_duty': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_patients': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '10'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to show only nurse users
        self.fields['nurse'].queryset = User.objects.filter(role=User.NURSE)


class PatientAdmissionForm(forms.ModelForm):
    """Form for patient admissions"""
    
    # Add custom patient field with search functionality
    patient_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search for patients by name, ID, or phone...',
            'id': 'patient-search-input',
            'autocomplete': 'off'
        }),
        label="Search Patients"
    )
    
    # Add custom bed field with search functionality
    bed_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search for available beds...',
            'id': 'bed-search-input',
            'autocomplete': 'off'
        }),
        label="Search Beds"
    )
    
    class Meta:
        model = PatientAdmission
        fields = [
            'patient', 'admitting_doctor', 'bed', 'admission_type',
            'primary_diagnosis', 'notes', 'is_critical'
        ]
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select', 'id': 'patient-select'}),
            'admitting_doctor': forms.Select(attrs={'class': 'form-select'}),
            'bed': forms.Select(attrs={'class': 'form-select', 'id': 'bed-select'}),
            'admission_type': forms.Select(attrs={'class': 'form-select'}),
            'primary_diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_critical': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter doctors to show only doctors
        self.fields['admitting_doctor'].queryset = User.objects.filter(role=User.DOCTOR, is_available=True)
        
        # Get all patients with better display information
        all_patients = Patient.objects.all().order_by('first_name', 'last_name')
        self.fields['patient'].queryset = all_patients
        
        # Create better labels for patients showing ID, name, age, and contact info
        patient_choices = []
        for patient in all_patients:
            age = patient.age if hasattr(patient, 'age') else 'N/A'
            blood_group = f" | {patient.blood_group}" if patient.blood_group else ""
            phone = f" | {patient.phone}" if patient.phone else ""
            label = f"{patient.patient_id} - {patient.full_name} ({age} yrs, {patient.get_gender_display()}{blood_group}{phone})"
            patient_choices.append((patient.id, label))
        
        if patient_choices:
            self.fields['patient'].choices = [('', '---------')] + patient_choices
        
        # Show only empty beds with detailed information
        available_beds = Bed.objects.filter(is_occupied=False).select_related('room')
        self.fields['bed'].queryset = available_beds
        
        # Create better labels for beds showing room and floor info
        bed_choices = []
        for bed in available_beds:
            label = f"Bed {bed.bed_number} - Room {bed.room.room_number} (Floor {bed.room.floor}, {bed.room.get_department_display()})"
            bed_choices.append((bed.id, label))
        
        if bed_choices:
            self.fields['bed'].choices = [('', '---------')] + bed_choices
    
    def clean(self):
        cleaned_data = super().clean()
        admission_type = cleaned_data.get('admission_type')
        admitting_doctor = cleaned_data.get('admitting_doctor')
        bed = cleaned_data.get('bed')
        is_critical = cleaned_data.get('is_critical')
        
        # For emergency admissions, validate doctor department matches room department
        if admission_type == PatientAdmission.EMERGENCY and admitting_doctor and bed:
            if bed.room.department and hasattr(admitting_doctor, 'department'):
                # Check if doctor department matches room's department
                if admission_type == PatientAdmission.EMERGENCY:
                    # For emergency, we're more flexible - just warn
                    if bed.room.department != getattr(admitting_doctor, 'department', None):
                        self.add_error(None, f"Warning: Doctor department does not match room department")
                else:
                    # For regular admissions, require matching department
                    if bed.room.department != getattr(admitting_doctor, 'department', None):
                        self.add_error('admitting_doctor', f"Doctor department does not match room department")
        
        return cleaned_data


class EmergencyAdmissionForm(PatientAdmissionForm):
    """Simplified form for emergency admissions"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set defaults for emergency
        self.fields['admission_type'].initial = PatientAdmission.EMERGENCY
        self.fields['is_critical'].initial = True
        
        # For emergency, we need any available doctor and bed
        self.fields['admitting_doctor'].queryset = User.objects.filter(role=User.DOCTOR, is_available=True)
        self.fields['bed'].queryset = Bed.objects.filter(is_occupied=False)
    
    class Meta(PatientAdmissionForm.Meta):
        fields = ['patient', 'admitting_doctor', 'bed', 'primary_diagnosis', 'is_critical']


class AdmissionRequestForm(forms.ModelForm):
    """Form for creating admission requests"""
    class Meta:
        model = AdmissionRequest
        fields = [
            'patient', 'primary_diagnosis', 'secondary_diagnosis', 
            'treatment_plan', 'estimated_length_of_stay', 
            'preferred_room_type', 'preferred_floor', 
            'special_requirements', 'priority'
        ]
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'primary_diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'secondary_diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'treatment_plan': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'estimated_length_of_stay': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'preferred_room_type': forms.Select(attrs={'class': 'form-select'}),
            'preferred_floor': forms.Select(attrs={'class': 'form-select'}),
            'special_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter patients to show only active patients
        self.fields['patient'].queryset = Patient.objects.all().order_by('first_name', 'last_name') 