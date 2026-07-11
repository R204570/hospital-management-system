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
from patient.selectors import find_available_doctor
from patient.selectors import find_available_nurse


@login_required
def admission_list(request):
    """View for listing patient admissions with search and floor-based filtering"""
    # Get all admissions with related data
    admissions = PatientAdmission.objects.select_related(
        'patient', 'admitting_doctor', 'assigned_nurse', 'bed__room'
    ).order_by('-admission_date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        admissions = admissions.filter(
            models.Q(patient__first_name__icontains=search_query) |
            models.Q(patient__last_name__icontains=search_query) |
            models.Q(patient__patient_id__icontains=search_query) |
            models.Q(primary_diagnosis__icontains=search_query) |
            models.Q(bed__room__room_number__icontains=search_query) |
            models.Q(admitting_doctor__first_name__icontains=search_query) |
            models.Q(admitting_doctor__last_name__icontains=search_query)
        )
    
    # Floor-based filtering for nurses - only show patients on their assigned floors
    if request.user.is_nurse:
        try:
            nurse_assignment = Nurse.objects.get(nurse=request.user)
            if nurse_assignment.assigned_floors:
                # For SQLite compatibility, use __in with the assigned floors list
                admissions = admissions.filter(bed__room__floor__in=nurse_assignment.assigned_floors)
        except Nurse.DoesNotExist:
            # If nurse assignment doesn't exist, show all admissions but add a warning
            messages.warning(request, 'You are not assigned to any floors. Please contact an administrator.')
    
    # Filter by doctor if user is a doctor  
    elif request.user.is_doctor:
        admissions = admissions.filter(admitting_doctor=request.user)
    
    # Filter options
    status = request.GET.get('status')
    doctor_id = request.GET.get('doctor')
    admission_type = request.GET.get('admission_type')
    floor_filter = request.GET.get('floor')
    department_filter = request.GET.get('department')
    
    # Apply filters
    if status == 'current':
        admissions = admissions.filter(discharge_date__isnull=True)
    elif status == 'discharged':
        admissions = admissions.filter(discharge_date__isnull=False)
    
    if doctor_id:
        admissions = admissions.filter(admitting_doctor_id=doctor_id)
    
    if admission_type:
        admissions = admissions.filter(admission_type=admission_type)
    
    # Floor filter (for admin/receptionist)
    if floor_filter and (request.user.is_admin or request.user.is_receptionist):
        admissions = admissions.filter(bed__room__floor=floor_filter)
    
    # Department filter
    if department_filter and (request.user.is_admin or request.user.is_receptionist):
        admissions = admissions.filter(bed__room__department=department_filter)
    
    # Get user's nurse assignment info for context
    user_nurse_assignment = None
    if request.user.is_nurse:
        try:
            user_nurse_assignment = Nurse.objects.get(nurse=request.user)
        except Nurse.DoesNotExist:
            pass
    
    context = {
        'admissions': admissions,
        'search_query': search_query,
        'status_filter': status,
        'doctor_filter': doctor_id,
        'admission_type_filter': admission_type,
        'floor_filter': floor_filter,
        'department_filter': department_filter,
        'doctors': User.objects.filter(role=User.DOCTOR),
        'admission_types': PatientAdmission.ADMISSION_TYPE_CHOICES,
        'floor_choices': [(i, f'Floor {i}') for i in range(1, 7)],
        'department_choices': Room.DEPARTMENT_CHOICES,
        'user_nurse_assignment': user_nurse_assignment,
    }
    
    return render(request, 'patient/admission_list.html', context)


@login_required
def admission_create(request, patient_id=None):
    """View for admitting a patient"""
    # Check if the user is a doctor
    if not request.user.is_doctor:
        messages.error(request, "Only doctors can admit patients.")
        return redirect('dashboard')
        
    patient = None
    if patient_id:
        patient = get_object_or_404(Patient, pk=patient_id)
    
    if request.method == 'POST':
        initial = {}
        if patient_id:
            initial['patient'] = get_object_or_404(Patient, pk=patient_id)
        if request.user.is_doctor:
            initial['admitting_doctor'] = request.user
            
        form = PatientAdmissionForm(request.POST, initial=initial)
        
        # Maintain field disabled states
        if patient_id:
            form.fields['patient'].disabled = True
            form.fields['patient_search'].disabled = True
        if request.user.is_doctor:
            form.fields['admitting_doctor'].disabled = True
            
        if form.is_valid():
            admission = form.save(commit=False)
            
            # If doctor field was disabled, manually set the admitting doctor
            if request.user.is_doctor and form.fields['admitting_doctor'].disabled:
                admission.admitting_doctor = request.user
            
            # If no nurse is assigned, find an available nurse
            if not admission.assigned_nurse:
                # Get the floor of the room
                floor = admission.bed.room.floor
                
                # Find an available nurse for this floor
                available_nurse = find_available_nurse(floor)
                if available_nurse:
                    admission.assigned_nurse = available_nurse.nurse
            
            # Set the created_by field to the current user
            admission.created_by = request.user
            
            admission.save()
            
            messages.success(request, f'Patient {admission.patient.full_name} admitted successfully.')
            return redirect('admission_detail', pk=admission.id)
    else:
        initial = {}
        if patient:
            initial['patient'] = patient
        
        # If doctor creating the admission, pre-select them as admitting doctor
        if request.user.is_doctor:
            initial['admitting_doctor'] = request.user
        
        form = PatientAdmissionForm(initial=initial)
        
        # If patient is provided, make the field read-only
        if patient:
            form.fields['patient'].disabled = True
            form.fields['patient_search'].disabled = True
            
        # If doctor creating the admission, make the admitting_doctor field read-only
        if request.user.is_doctor:
            form.fields['admitting_doctor'].disabled = True
    
    context = {
        'form': form,
        'title': 'Admit Patient',
        'patient': patient,
    }
    
    return render(request, 'patient/admission_form.html', context)


@login_required
def admission_detail(request, pk):
    """View for admission details"""
    admission = get_object_or_404(PatientAdmission, pk=pk)
    
    context = {
        'admission': admission,
    }
    
    return render(request, 'patient/admission_detail.html', context)


@doctor_required
def admission_discharge(request, pk):
    """View for discharging a patient"""
    admission = get_object_or_404(PatientAdmission, pk=pk)
    
    # Only allow discharge if not already discharged
    if admission.discharge_date:
        messages.error(request, 'This patient has already been discharged.')
        return redirect('admission_detail', pk=admission.id)
    
    if request.method == 'POST':
        # Discharge the patient
        admission.discharge()
        messages.success(request, f'Patient {admission.patient.full_name} discharged successfully.')
        return redirect('admission_list')
    
    context = {
        'admission': admission,
    }
    
    return render(request, 'patient/admission_discharge.html', context)


@login_required
def emergency_admission(request):
    """View for emergency patient admissions"""
    if request.method == 'POST':
        initial = {}
        if request.user.is_doctor:
            initial['admitting_doctor'] = request.user
            
        form = EmergencyAdmissionForm(request.POST, initial=initial)
        
        # Maintain field disabled states for emergency admission
        if request.user.is_doctor:
            form.fields['admitting_doctor'].disabled = True
            
        if form.is_valid():
            admission = form.save(commit=False)
            admission.admission_type = PatientAdmission.EMERGENCY
            admission.created_by = request.user
            
            # If doctor field was disabled, manually set the admitting doctor
            if request.user.is_doctor and form.fields['admitting_doctor'].disabled:
                admission.admitting_doctor = request.user
            
            # For emergency admissions, find an available doctor and nurse
            if not admission.admitting_doctor:
                # Get a doctor based on the specialty needed
                specialty = admission.bed.room.department
                available_doctor = find_available_doctor(specialty)
                
                if available_doctor:
                    admission.admitting_doctor = available_doctor
                else:
                    # If no doctor with matching specialty, get any available doctor
                    any_doctor = User.objects.filter(
                        role=User.DOCTOR, 
                        is_available=True
                    ).first()
                    
                    if any_doctor:
                        admission.admitting_doctor = any_doctor
                    else:
                        messages.error(request, 'No available doctors for emergency admission.')
                        return redirect('emergency_admission')
            
            # Find an available nurse
            if not admission.assigned_nurse:
                floor = admission.bed.room.floor
                available_nurse = find_available_nurse(floor)
                
                if available_nurse:
                    admission.assigned_nurse = available_nurse.nurse
            
            # Set doctor availability time (unavailable for 30 mins)
            admission.doctor_availability_time = timezone.now() + timezone.timedelta(minutes=30)
            
            # Save the admission
            admission.save()
            
            # Mark the doctor as unavailable for 30 minutes
            if admission.admitting_doctor:
                admission.admitting_doctor.is_available = False
                admission.admitting_doctor.save()
                
                # We'll need a background task to reset this after 30 minutes
                # In a real implementation, use Celery or other task queue
                # For now, just note that the doctor will be unavailable
            
            messages.success(request, f'Emergency admission for {admission.patient.full_name} created successfully.')
            return redirect('admission_detail', pk=admission.id)
    else:
        initial = {}
        if request.user.is_doctor:
            initial['admitting_doctor'] = request.user
            
        form = EmergencyAdmissionForm(initial=initial)
        
        # If doctor creating the admission, make the admitting_doctor field read-only
        if request.user.is_doctor:
            form.fields['admitting_doctor'].disabled = True
    
    context = {
        'form': form,
        'title': 'Emergency Admission',
        'is_emergency': True
    }
    
    return render(request, 'patient/admission_form.html', context)
