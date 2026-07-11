from django import forms
from patient.models import Patient, MedicalRecord, Room, Bed, Nurse, PatientAdmission, AdmissionRequest
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
