from django import forms
from patient.models import Patient, MedicalRecord, Room, Bed, Nurse, PatientAdmission, AdmissionRequest
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div
from datetime import datetime
from users.models import User


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
