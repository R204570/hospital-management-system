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
def create_medical_record(request, patient_id=None, appointment_id=None):
    """View for creating medical records"""
    patient = None
    appointment = None
    
    # Get patient object if patient_id is provided
    if patient_id:
        patient = get_object_or_404(Patient, pk=patient_id)
    
    # Get appointment object if appointment_id is provided
    if appointment_id:
        appointment = get_object_or_404(Appointment, pk=appointment_id)
        patient = appointment.patient
    
    # Initialize form with patient data
    initial_data = {}
    if patient:
        initial_data['patient'] = patient
    
    if request.method == 'POST':
        form = MedicalRecordForm(request.POST, request.FILES, initial=initial_data)
        if form.is_valid():
            record = form.save(commit=False)
            
            # Set doctor (current user if doctor, or from the appointment)
            if request.user.is_doctor:
                record.doctor = request.user
            elif appointment and appointment.doctor:
                record.doctor = appointment.doctor
            
            # Set appointment relation if available
            if appointment:
                record.appointment = appointment
            
            record.save()
            messages.success(request, 'Medical record created successfully')
            return redirect('patient_detail', pk=record.patient.id)
    else:
        form = MedicalRecordForm(initial=initial_data)
        
        # Set initial values for appointment-based records
        if appointment:
            form.fields['patient'].disabled = True
            
    context = {
        'form': form,
        'patient': patient,
        'appointment': appointment,
    }
    
    return render(request, 'patient/create_medical_record.html', context)


@login_required
def view_medical_record(request, record_id):
    """View for displaying a medical record"""
    record = get_object_or_404(MedicalRecord, id=record_id)
    
    return render(request, 'patient/view_medical_record.html', {'record': record})


@doctor_required
def update_medical_record(request, record_id):
    """View for doctors to update medical records"""
    record = get_object_or_404(MedicalRecord, id=record_id)
    
    # Only allow the doctor who created the record to edit it
    if record.doctor != request.user:
        messages.error(request, "You don't have permission to edit this record")
        return redirect('view_medical_record', record_id=record.id)
    
    if request.method == 'POST':
        # Pass doctor to the form and include request.FILES for file uploads
        form = MedicalRecordForm(request.POST, request.FILES, instance=record, doctor=request.user)
        
        if form.is_valid():
            # Save without committing to set additional fields
            updated_record = form.save(commit=False)
            # Ensure doctor remains the same
            updated_record.doctor = request.user
            # Ensure patient remains the same
            updated_record.patient = record.patient
            # Save the record
            updated_record.save()
            
            messages.success(request, 'Medical record updated successfully')
            return redirect('view_medical_record', record_id=record.id)
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        # Pass doctor to the form
        form = MedicalRecordForm(instance=record, doctor=request.user)
        
        # Hide the patient field completely (will still be in the form data)
        form.fields['patient'].widget = forms.HiddenInput()
    
    context = {
        'form': form,
        'record': record,
        'patient': record.patient,  # Add patient to context
    }
    
    return render(request, 'patient/update_medical_record.html', context)


@login_required
def medical_record_pdf(request, record_id):
    """Generate PDF for a medical record"""
    record = get_object_or_404(MedicalRecord, id=record_id)
    
    # Prepare context for PDF template
    context = {'record': record}
    
    # Render the template
    template = get_template('patient/medical_record_pdf.html')
    html = template.render(context)
    
    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    filename = f"medical_record_{record.patient.patient_id}_{record.report_date.strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Generate PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('PDF generation error', content_type='text/plain')
    
    return response


@doctor_required
def delete_medical_record(request, record_id):
    """View for deleting a medical record"""
    record = get_object_or_404(MedicalRecord, id=record_id)
    
    # Only allow the doctor who created the record to delete it
    if record.doctor != request.user:
        messages.error(request, "You don't have permission to delete this record")
        return redirect('view_medical_record', record_id=record.id)
    
    if request.method == 'POST':
        patient_id = record.patient.id
        record.delete()
        messages.success(request, 'Medical record deleted successfully')
        return redirect('patient_detail', pk=patient_id)
    
    # If not POST request, redirect to the record view
    return redirect('view_medical_record', record_id=record.id)


@login_required
def recent_medical_records(request):
    """View for listing recent medical records with filtering options"""
    user = request.user
    
    # Filter records based on user role
    if user.is_doctor:
        records = MedicalRecord.objects.filter(doctor=user)
    elif user.is_receptionist or user.is_admin:
        records = MedicalRecord.objects.all()
    else:
        # Nurses and others see all records, but could be limited as needed
        records = MedicalRecord.objects.all()
    
    # Apply date filter if provided
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            records = records.filter(report_date__date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            records = records.filter(report_date__date__lte=date_to)
        except ValueError:
            pass
    
    # Apply patient filter if provided
    patient_id = request.GET.get('patient')
    if patient_id:
        records = records.filter(patient_id=patient_id)
    
    # Order by most recent first
    records = records.order_by('-report_date')
    
    # Pagination
    paginator = Paginator(records, 15)  # Show 15 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'medical_records': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
    }
    
    return render(request, 'patient/recent_medical_records.html', context)
