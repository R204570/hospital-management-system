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


@login_required
def patient_list(request):
    """View for listing and searching patients"""
    # Only allow doctors, receptionists, nurses and admins to access this view
    if not (request.user.is_doctor or request.user.is_receptionist or 
            request.user.is_nurse or request.user.is_admin):
        messages.error(request, "You don't have permission to view the patient list.")
        return redirect('dashboard')
    
    # Debug messages to check if doctors are being redirected
    if request.user.is_doctor:
        print(f"Doctor {request.user.username} accessed patient_list")
    
    # Get search query directly from URL parameter
    search_query = request.GET.get('search', '').strip()
    patients = Patient.objects.all().order_by('-registration_date')
    
    # Apply search filters if provided
    if search_query:
        patients = patients.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) | 
            Q(patient_id__icontains=search_query) | 
            Q(phone__icontains=search_query)
        )
    
    context = {
        'patients': patients,
        'search_query': search_query,
    }
    
    # Add this to debug
    if search_query:
        print(f"Search query: '{search_query}' - Found {len(patients)} patients")
    else:
        print(f"No search query - Showing all {len(patients)} patients")
    
    return render(request, 'patient/patient_list.html', context)


@receptionist_required
def patient_register(request):
    """View for registering new patients"""
    if request.method == 'POST':
        # Check if we have cropped image data
        cropped_data = request.POST.get('cropped_data')
        
        if cropped_data and cropped_data.startswith('data:image'):
            # There's cropped image data, process it and create a file
            try:
                # Get the content after the comma
                format, imgstr = cropped_data.split(';base64,')
                ext = format.split('/')[-1]
                
                # Generate a random filename
                filename = f"{uuid.uuid4()}.{ext}"
                temp_file_path = os.path.join(settings.MEDIA_ROOT, 'temp', filename)
                
                # Ensure the temp directory exists
                os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
                
                # Save the decoded image data to a file
                with open(temp_file_path, 'wb') as f:
                    f.write(base64.b64decode(imgstr))
                
                # Create a file object to save to model
                with open(temp_file_path, 'rb') as f:
                    # Replace the profile_picture field in request.FILES
                    from django.core.files.uploadedfile import SimpleUploadedFile
                    request.FILES['profile_picture'] = SimpleUploadedFile(
                        name=filename,
                        content=f.read(),
                        content_type=format.split(':')[1]
                    )
                
                # Remove the temporary file
                os.remove(temp_file_path)
                
            except (binascii.Error, IOError, OSError) as e:
                print(f"Error processing cropped image: {str(e)}")
                messages.error(request, f"Error processing cropped image: {str(e)}")
                # Continue without the cropped image
                
        form = PatientRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            patient = form.save()
            messages.success(request, f'Patient registered successfully with ID: {patient.patient_id}')
            return redirect('patient_detail', pk=patient.id)
    else:
        form = PatientRegistrationForm()
    
    return render(request, 'patient/patient_register.html', {'form': form})


@login_required
def patient_detail(request, pk):
    """View for displaying patient details"""
    patient = get_object_or_404(Patient, pk=pk)
    medical_records = patient.medical_records.all()
    
    # Get admissions for this patient
    admissions = PatientAdmission.objects.filter(patient=patient).order_by('-admission_date')
    current_admission = admissions.filter(discharge_date__isnull=True).first()
    
    context = {
        'patient': patient,
        'medical_records': medical_records,
        'admissions': admissions,
        'current_admission': current_admission,
    }
    
    return render(request, 'patient/patient_detail.html', context)


@receptionist_required
def patient_update(request, pk):
    """View for updating patient information"""
    patient = get_object_or_404(Patient, pk=pk)
    
    if request.method == 'POST':
        # Check if we have cropped image data
        cropped_data = request.POST.get('cropped_data')
        
        if cropped_data and cropped_data.startswith('data:image'):
            # There's cropped image data, process it and create a file
            try:
                # Get the content after the comma
                format, imgstr = cropped_data.split(';base64,')
                ext = format.split('/')[-1]
                
                # Generate a random filename
                filename = f"{uuid.uuid4()}.{ext}"
                temp_file_path = os.path.join(settings.MEDIA_ROOT, 'temp', filename)
                
                # Ensure the temp directory exists
                os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
                
                # Save the decoded image data to a file
                with open(temp_file_path, 'wb') as f:
                    f.write(base64.b64decode(imgstr))
                
                # Create a file object to save to model
                with open(temp_file_path, 'rb') as f:
                    # Replace the profile_picture field in request.FILES
                    from django.core.files.uploadedfile import SimpleUploadedFile
                    request.FILES['profile_picture'] = SimpleUploadedFile(
                        name=filename,
                        content=f.read(),
                        content_type=format.split(':')[1]
                    )
                
                # Remove the temporary file
                os.remove(temp_file_path)
                
            except (binascii.Error, IOError, OSError) as e:
                print(f"Error processing cropped image: {str(e)}")
                messages.error(request, f"Error processing cropped image: {str(e)}")
                # Continue without the cropped image
                
        form = PatientRegistrationForm(request.POST, request.FILES, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Patient information updated successfully')
            return redirect('patient_detail', pk=patient.id)
    else:
        form = PatientRegistrationForm(instance=patient)
    
    return render(request, 'patient/patient_update.html', {'form': form, 'patient': patient})


@login_required
def patient_list_ajax(request):
    """AJAX-enhanced patient list view"""
    # Only allow doctors, receptionists, nurses and admins to access this view
    if not (request.user.is_doctor or request.user.is_receptionist or 
            request.user.is_nurse or request.user.is_admin):
        messages.error(request, "You don't have permission to view the patient list.")
        return redirect('dashboard')
    
    patients = Patient.objects.all().order_by('-registration_date')
    
    context = {
        'patients': patients,
    }
    
    return render(request, 'patient/patient_list_ajax.html', context)


@login_required
def patient_search_api(request):
    """AJAX endpoint for patient search"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search patients by name, patient_id, or phone
    patients = Patient.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(patient_id__icontains=query) |
        Q(phone__icontains=query)
    ).order_by('first_name', 'last_name')[:20]  # Limit to 20 results
    
    results = []
    for patient in patients:
        age = patient.age if hasattr(patient, 'age') else 'N/A'
        blood_group = f" | {patient.blood_group}" if patient.blood_group else ""
        phone = f" | {patient.phone}" if patient.phone else ""
        
        results.append({
            'id': patient.id,
            'text': f"{patient.patient_id} - {patient.full_name} ({age} yrs, {patient.get_gender_display()}{blood_group}{phone})",
            'patient_id': patient.patient_id,
            'name': patient.full_name,
            'age': age,
            'gender': patient.get_gender_display(),
            'blood_group': patient.blood_group or '',
            'phone': patient.phone or ''
        })
    
    return JsonResponse({'results': results})
