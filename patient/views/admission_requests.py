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


@doctor_required
def admission_request_create(request, patient_id=None):
    """View for doctors to create admission requests"""
    patient = None
    if patient_id:
        patient = get_object_or_404(Patient, pk=patient_id)
    
    if request.method == 'POST':
        form = AdmissionRequestForm(request.POST)
        if form.is_valid():
            admission_request = form.save(commit=False)
            admission_request.requesting_doctor = request.user
            admission_request.save()
            
            messages.success(request, f'Admission request submitted for {admission_request.patient.full_name}')
            return redirect('admission_request_detail', pk=admission_request.id)
    else:
        initial = {}
        if patient:
            initial['patient'] = patient
        form = AdmissionRequestForm(initial=initial)
    
    context = {
        'form': form,
        'patient': patient,
        'title': 'Create Admission Request'
    }
    
    return render(request, 'patient/admission_request_form.html', context)


@login_required
def admission_request_list(request):
    """View for listing admission requests with search and filtering"""
    requests = AdmissionRequest.objects.select_related(
        'patient', 'requesting_doctor', 'reviewed_by'
    ).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        requests = requests.filter(
            Q(patient__first_name__icontains=search_query) |
            Q(patient__last_name__icontains=search_query) |
            Q(patient__patient_id__icontains=search_query) |
            Q(primary_diagnosis__icontains=search_query) |
            Q(requesting_doctor__first_name__icontains=search_query) |
            Q(requesting_doctor__last_name__icontains=search_query)
        )
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        requests = requests.filter(status=status)
    
    # Filter by priority for nurses/admin
    if request.user.is_nurse or request.user.is_admin:
        priority = request.GET.get('priority')
        if priority:
            requests = requests.filter(priority=priority)
    
    # Floor filtering for nurses - show requests for floors they handle
    if request.user.is_nurse:
        try:
            nurse_assignment = Nurse.objects.get(nurse=request.user)
            if nurse_assignment.assigned_floors:
                # Show requests where preferred floor is in nurse's assignment
                # or where no floor preference is specified (they can handle any)
                requests = requests.filter(
                    Q(preferred_floor__in=nurse_assignment.assigned_floors) |
                    Q(preferred_floor__isnull=True)
                )
        except Nurse.DoesNotExist:
            messages.warning(request, 'You are not assigned to any floors. Please contact an administrator.')
    
    # Doctors see only their requests
    elif request.user.is_doctor:
        requests = requests.filter(requesting_doctor=request.user)
    
    # Floor and department filters for admin/receptionist
    floor_filter = request.GET.get('floor')
    if floor_filter and (request.user.is_admin or request.user.is_receptionist):
        requests = requests.filter(preferred_floor=floor_filter)
    
    context = {
        'admission_requests': requests,
        'search_query': search_query,
        'status_filter': status,
        'floor_filter': floor_filter,
        'status_choices': AdmissionRequest.STATUS_CHOICES,
        'priority_choices': AdmissionRequest.PRIORITY_CHOICES,
        'floor_choices': [(i, f'Floor {i}') for i in range(1, 7)],
    }
    
    return render(request, 'patient/admission_request_list.html', context)


@login_required
def admission_request_detail(request, pk):
    """View for admission request details"""
    admission_request = get_object_or_404(AdmissionRequest, pk=pk)
    
    context = {
        'admission_request': admission_request,
    }
    
    return render(request, 'patient/admission_request_detail.html', context)


@nurse_required
def admission_request_process(request, pk):
    """View for nurses to process admission requests (assign rooms)"""
    admission_request = get_object_or_404(AdmissionRequest, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            admission_request.status = AdmissionRequest.APPROVED
            admission_request.reviewed_by = request.user
            admission_request.reviewed_at = timezone.now()
            admission_request.review_notes = request.POST.get('review_notes', '')
            admission_request.save()
            
            messages.success(request, 'Admission request approved. Please assign a room.')
            return redirect('admission_request_assign_room', pk=pk)
            
        elif action == 'reject':
            admission_request.status = AdmissionRequest.REJECTED
            admission_request.reviewed_by = request.user
            admission_request.reviewed_at = timezone.now()
            admission_request.review_notes = request.POST.get('review_notes', '')
            admission_request.save()
            
            messages.success(request, 'Admission request rejected.')
            return redirect('admission_request_list')
    
    # Get available beds for the preferred room type and floor
    available_beds = Bed.objects.filter(
        is_occupied=False,
        is_functional=True,
        room__is_active=True
    )
    
    if admission_request.preferred_room_type:
        available_beds = available_beds.filter(room__room_type=admission_request.preferred_room_type)
    
    if admission_request.preferred_floor:
        available_beds = available_beds.filter(room__floor=admission_request.preferred_floor)
    
    context = {
        'admission_request': admission_request,
        'available_beds': available_beds[:10],  # Show top 10 options
    }
    
    return render(request, 'patient/admission_request_process.html', context)


@nurse_required
def admission_request_assign_room(request, pk):
    """View for nurses to assign room to approved admission requests"""
    admission_request = get_object_or_404(AdmissionRequest, pk=pk)
    
    if admission_request.status != AdmissionRequest.APPROVED:
        messages.error(request, 'This admission request is not approved for room assignment.')
        return redirect('admission_request_detail', pk=pk)
    
    if request.method == 'POST':
        bed_id = request.POST.get('bed_id')
        bed = get_object_or_404(Bed, pk=bed_id, is_occupied=False)
        
        # Create the patient admission
        patient_admission = PatientAdmission.objects.create(
            patient=admission_request.patient,
            admitting_doctor=admission_request.requesting_doctor,
            bed=bed,
            assigned_nurse=request.user,
            primary_diagnosis=admission_request.primary_diagnosis,
            secondary_diagnosis=admission_request.secondary_diagnosis,
            treatment_plan=admission_request.treatment_plan,
            admission_type=PatientAdmission.REGULAR,
            assigned_by=request.user,
            created_by=request.user,
        )
        
        # Update admission request
        admission_request.status = AdmissionRequest.COMPLETED
        admission_request.completed_at = timezone.now()
        admission_request.patient_admission = patient_admission
        admission_request.save()
        
        # Mark bed as occupied
        bed.is_occupied = True
        bed.save()
        
        messages.success(request, f'Patient {admission_request.patient.full_name} admitted to {bed.room.room_number}-{bed.bed_number}')
        return redirect('admission_detail', pk=patient_admission.id)
    
    # Get available beds
    available_beds = Bed.objects.filter(
        is_occupied=False,
        is_functional=True,
        room__is_active=True
    ).select_related('room')
    
    # Apply preferences if specified
    if admission_request.preferred_room_type:
        available_beds = available_beds.filter(room__room_type=admission_request.preferred_room_type)
    
    if admission_request.preferred_floor:
        available_beds = available_beds.filter(room__floor=admission_request.preferred_floor)
    
    context = {
        'admission_request': admission_request,
        'available_beds': available_beds,
    }
    
    return render(request, 'patient/admission_request_assign_room.html', context)
