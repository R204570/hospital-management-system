from django import forms
from patient.models import Patient, MedicalRecord, Room, Bed, Nurse, PatientAdmission, AdmissionRequest
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div
from datetime import datetime
from users.models import User


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
