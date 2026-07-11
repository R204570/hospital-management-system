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


@nurse_required
def nurse_prescription_list(request):
    """View for nurses to list prescriptions from medical records"""
    status_filter = request.GET.get('status', '')
    
    # Get medical records with prescriptions
    records = MedicalRecord.objects.exclude(prescription='').order_by('-report_date')
    
    # Filter by status if provided
    if status_filter == 'pending':
        # Simple implementation - in a real system you'd have a proper status field
        pass
    
    # Pagination
    paginator = Paginator(records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'active_tab': 'prescriptions'
    }
    
    return render(request, 'patient/nurse_prescription_list.html', context)


@nurse_required
def nurse_prescription_detail(request, pk):
    """View for nurses to view prescription details"""
    record = get_object_or_404(MedicalRecord, pk=pk)
    
    # Get medications that might be related to the prescription
    from pharmacy.models import MedicineItem
    medicines = MedicineItem.objects.filter(is_active=True)
    
    context = {
        'record': record,
        'medicines': medicines,
        'active_tab': 'prescriptions'
    }
    
    return render(request, 'patient/nurse_prescription_detail.html', context)


@nurse_required
def nurse_medication_administration(request, record_id):
    """View for nurses to record medication administration"""
    record = get_object_or_404(MedicalRecord, pk=record_id)
    
    if request.method == 'POST':
        # Get form data
        medication_name = request.POST.get('medication_name')
        dose_given = request.POST.get('dose_given')
        administration_time = timezone.now()
        notes = request.POST.get('notes', '')
        
        # Simple implementation - in a real system, you'd have a MedicationAdministration model
        # Here we're just storing it in a notes field as a demonstration
        admin_record = f"\n[{administration_time.strftime('%Y-%m-%d %H:%M')}] {medication_name} - {dose_given} administered by {request.user.get_full_name()}."
        if notes:
            admin_record += f" Notes: {notes}"
        
        # Add the administration record to notes
        if not record.notes:
            record.notes = "MEDICATION ADMINISTRATION LOG:"
        record.notes += admin_record
        record.save()
        
        messages.success(request, f"{medication_name} administration recorded successfully.")
        return redirect('nurse_prescription_detail', pk=record.id)
    
    context = {
        'record': record,
        'active_tab': 'prescriptions'
    }
    
    return render(request, 'patient/nurse_medication_administration.html', context)
