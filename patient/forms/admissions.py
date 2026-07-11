from django import forms
from patient.models import Patient, MedicalRecord, Room, Bed, Nurse, PatientAdmission, AdmissionRequest
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div
from datetime import datetime
from users.models import User


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
        # Set defaults for emergency (admission_type is forced in the view on save,
        # and is intentionally not one of this simplified form's fields).
        if 'admission_type' in self.fields:
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
