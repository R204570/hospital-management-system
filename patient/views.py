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

from .models import Patient, MedicalRecord, Room, Bed, Nurse, PatientAdmission, AdmissionRequest
from .forms import (
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


# Room Management Views
@admin_required
def room_list(request):
    """View for listing all rooms"""
    rooms = Room.objects.all().order_by('floor', 'room_number')
    
    # Add bed count and occupancy to rooms
    for room in rooms:
        room.bed_count = room.beds.count()
        room.occupied_beds = room.beds.filter(is_occupied=True).count()
    
    context = {
        'rooms': rooms,
    }
    
    return render(request, 'patient/room_list.html', context)


@admin_required
def room_create(request):
    """View for creating a new room"""
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save()
            
            # Create default beds (10 per room)
            for i in range(1, 11):
                Bed.objects.create(
                    room=room,
                    bed_number=f"B{i:02d}"
                )
            
            messages.success(request, f'Room {room.room_number} created successfully with 10 beds.')
            return redirect('room_detail', pk=room.id)
    else:
        form = RoomForm()
    
    context = {
        'form': form,
        'title': 'Create New Room'
    }
    
    return render(request, 'patient/room_form.html', context)


@admin_required
def room_detail(request, pk):
    """View for room details"""
    room = get_object_or_404(Room, pk=pk)
    beds = room.beds.all()
    
    # Get current admissions for occupied beds
    for bed in beds:
        if bed.is_occupied:
            bed.current_admission = PatientAdmission.objects.filter(
                bed=bed, 
                discharge_date__isnull=True
            ).first()
    
    context = {
        'room': room,
        'beds': beds
    }
    
    return render(request, 'patient/room_detail.html', context)


@admin_required
def room_update(request, pk):
    """View for updating room details"""
    room = get_object_or_404(Room, pk=pk)
    
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, f'Room {room.room_number} updated successfully.')
            return redirect('room_detail', pk=room.id)
    else:
        form = RoomForm(instance=room)
    
    context = {
        'form': form,
        'title': f'Update Room {room.room_number}',
        'room': room
    }
    
    return render(request, 'patient/room_form.html', context)


# Bed Management Views
@login_required
def bed_list(request):
    """View for listing all beds with their status"""
    beds = Bed.objects.all().select_related('room')
    
    # Filter options
    floor = request.GET.get('floor')
    status = request.GET.get('status')
    department = request.GET.get('department')
    
    if floor:
        beds = beds.filter(room__floor=floor)
    
    if status == 'available':
        beds = beds.filter(is_occupied=False)
    elif status == 'occupied':
        beds = beds.filter(is_occupied=True)
    
    if department:
        beds = beds.filter(room__department=department)
    
    # Add current patient info to occupied beds
    for bed in beds:
        if bed.is_occupied:
            bed.current_admission = PatientAdmission.objects.filter(
                bed=bed,
                discharge_date__isnull=True
            ).first()
    
    context = {
        'beds': beds,
        'floor_filter': floor,
        'status_filter': status,
        'department_filter': department,
        'department_choices': Room.DEPARTMENT_CHOICES,
    }
    
    return render(request, 'patient/bed_list.html', context)


@admin_required
def bed_create(request, room_id=None):
    """View for creating a new bed"""
    room = None
    if room_id:
        room = get_object_or_404(Room, pk=room_id)
    
    if request.method == 'POST':
        form = BedForm(request.POST)
        if form.is_valid():
            bed = form.save()
            messages.success(request, f'Bed {bed.bed_number} in Room {bed.room.room_number} created successfully.')
            
            if room:
                return redirect('room_detail', pk=room.id)
            return redirect('bed_list')
    else:
        initial = {}
        if room:
            initial['room'] = room
        form = BedForm(initial=initial)
    
    context = {
        'form': form,
        'title': 'Create New Bed',
        'room': room
    }
    
    return render(request, 'patient/bed_form.html', context)


@admin_required
def bed_update(request, pk):
    """View for updating bed details"""
    bed = get_object_or_404(Bed, pk=pk)
    
    if request.method == 'POST':
        form = BedForm(request.POST, instance=bed)
        if form.is_valid():
            form.save()
            messages.success(request, f'Bed {bed.bed_number} updated successfully.')
            return redirect('room_detail', pk=bed.room.id)
    else:
        form = BedForm(instance=bed)
    
    context = {
        'form': form,
        'title': f'Update Bed {bed.bed_number}',
        'bed': bed
    }
    
    return render(request, 'patient/bed_form.html', context)


# Patient Admission Views
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
                available_nurse = _find_available_nurse(floor)
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
                available_doctor = _find_available_doctor(specialty)
                
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
                available_nurse = _find_available_nurse(floor)
                
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


# Helper functions
def _find_available_nurse(floor):
    """Find an available nurse for the given floor"""
    # Get nurses assigned to this floor who are on duty
    available_nurses = Nurse.objects.filter(
        floor=floor,
        is_on_duty=True
    )
    
    # Find nurses with less than max patients
    for nurse in available_nurses:
        if nurse.is_available:
            return nurse
    
    # If no nurses found with capacity, return the one with fewest patients
    if available_nurses:
        return min(
            available_nurses, 
            key=lambda n: PatientAdmission.objects.filter(
                assigned_nurse=n.nurse, 
                discharge_date__isnull=True
            ).count()
        )
    
    return None


def _find_available_doctor(specialty=None):
    """Find an available doctor matching the specialty"""
    doctors_query = User.objects.filter(
        role=User.DOCTOR,
        is_available=True
    )
    
    if specialty:
        # First try to find a doctor with matching specialty
        specialty_doctors = doctors_query.filter(department=specialty)
        if specialty_doctors.exists():
            return specialty_doctors.first()
    
    # If no specialty match or no specialty provided, get any available doctor
    if doctors_query.exists():
        return doctors_query.first()
    
    return None


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
def assigned_patients(request):
    """View doctors' assigned patients (patients who had appointments with the doctor)"""
    # Get unique patients who had appointments with this doctor
    patients = Patient.objects.filter(
        appointment__doctor=request.user
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
            appointment__doctor=user
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


def extract_common_keywords(diagnoses, limit=10):
    """Helper function to extract common keywords from diagnoses"""
    # This is a simple implementation - in a real system, you'd use NLP techniques
    all_words = []
    for diagnosis in diagnoses:
        # Split by spaces and punctuation
        words = re.findall(r'\b\w+\b', diagnosis.lower())
        all_words.extend(words)
    
    # Remove common English stopwords
    stopwords = {'the', 'and', 'or', 'a', 'an', 'of', 'to', 'with', 'in', 'on', 'for'}
    filtered_words = [word for word in all_words if word not in stopwords and len(word) > 2]
    
    # Count occurrences and return most common
    word_counts = Counter(filtered_words)
    return word_counts.most_common(limit)


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


# Admission Request Views
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


@login_required
def bed_search_api(request):
    """AJAX endpoint for bed search"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    # Search available beds by bed number, room number, floor, or department
    beds = Bed.objects.filter(
        is_occupied=False
    ).select_related('room').filter(
        Q(bed_number__icontains=query) |
        Q(room__room_number__icontains=query) |
        Q(room__floor__icontains=query) |
        Q(room__department__icontains=query)
    ).order_by('room__floor', 'room__room_number', 'bed_number')[:20]  # Limit to 20 results
    
    results = []
    for bed in beds:
        results.append({
            'id': bed.id,
            'text': f"Bed {bed.bed_number} - Room {bed.room.room_number} (Floor {bed.room.floor}, {bed.room.get_department_display()})",
            'bed_number': bed.bed_number,
            'room_number': bed.room.room_number,
            'floor': bed.room.floor,
            'department': bed.room.get_department_display()
        })
    
    return JsonResponse({'results': results}) 