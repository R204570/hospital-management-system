from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.http import HttpResponse, Http404, JsonResponse
from django.utils import timezone
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.core.paginator import Paginator
import re
from collections import Counter
from datetime import datetime, timedelta
from django import forms
import os
import uuid
import base64
import binascii
from django.conf import settings

from patient.models import Patient, MedicalRecord, Room, Bed, Nurse, PatientAdmission, AdmissionRequest
from patient.forms import (
    PatientRegistrationForm, PatientSearchForm, MedicalRecordForm, 
    MedicalRecordFilterForm, RoomForm, BedForm, NurseAssignmentForm,
    PatientAdmissionForm, EmergencyAdmissionForm, AdmissionRequestForm
)
from users.decorators import receptionist_required, doctor_required, admin_required, nurse_required
from users.models import User
from appointment.models import Appointment
from patient.services import extract_common_keywords


@doctor_required
def assigned_patients(request):
    """View doctors' assigned patients (patients who had appointments with the doctor)"""
    # Get unique patients who had appointments with this doctor
    patients = Patient.objects.filter(
        appointments__doctor=request.user
    ).distinct()
    
    # Annotate patients with their last appointment date
    for patient in patients:
        patient.last_appointment = Appointment.objects.filter(
            doctor=request.user,
            patient=patient
        ).order_by('-date').first()
    
    context = {
        'patients': patients,
        'show_all_patients_link': True,  # Add this to show link to all patients
    }
    
    return render(request, 'patient/assigned_patients.html', context)


@login_required
def pdf_reports(request):
    """View for generating and downloading PDF reports"""
    user = request.user
    
    # Filter records based on user role
    if user.is_doctor:
        records = MedicalRecord.objects.filter(doctor=user)
    elif user.is_receptionist or user.is_admin:
        records = MedicalRecord.objects.all()
    else:
        records = MedicalRecord.objects.all()
    
    # Get the most recent 20 records
    recent_records = records.order_by('-report_date')[:20]
    
    context = {
        'records': recent_records,
    }
    
    return render(request, 'patient/pdf_reports.html', context)


@login_required
def patient_statistics(request):
    """View for displaying patient statistics"""
    user = request.user
    
    # General statistics
    total_patients = Patient.objects.count()
    
    # Doctor-specific statistics
    if user.is_doctor:
        assigned_patients_count = Patient.objects.filter(
            appointments__doctor=user
        ).distinct().count()
        
        records_created = MedicalRecord.objects.filter(doctor=user).count()
        
        recent_appointments = Appointment.objects.filter(
            doctor=user,
            date__gte=timezone.now().date() - timezone.timedelta(days=30)
        ).count()
        
        # Get disease distribution
        diagnoses = MedicalRecord.objects.filter(
            doctor=user
        ).values_list('diagnosis', flat=True)
        
        # This is a simple approach - in a real system you'd want more sophisticated analysis
        common_keywords = extract_common_keywords(diagnoses)
        
    else:
        # For non-doctors, show general statistics
        assigned_patients_count = None
        records_created = MedicalRecord.objects.count()
        recent_appointments = Appointment.objects.filter(
            date__gte=timezone.now().date() - timezone.timedelta(days=30)
        ).count()
        common_keywords = None
    
    context = {
        'total_patients': total_patients,
        'assigned_patients_count': assigned_patients_count,
        'records_created': records_created,
        'recent_appointments': recent_appointments,
        'common_keywords': common_keywords,
    }
    
    return render(request, 'patient/patient_statistics.html', context)
