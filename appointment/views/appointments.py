from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
import datetime
import json
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import logging
from django.core.paginator import Paginator
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from appointment.models import Appointment, DoctorAvailability, DoctorLeaveRequest
from appointment.forms import AppointmentForm, TimeSlotForm, DoctorAvailabilityForm, AppointmentStatusForm, DoctorLeaveRequestForm, LeaveRequestReviewForm
from patient.models import Patient
from users.models import User
from users.decorators import doctor_required, receptionist_required, nurse_required, pharmacist_required, admin_required, role_required
from website.models import AppointmentInquiry, ContactInquiry


@login_required
def appointment_list(request):
    """View for listing appointments with filters"""
    user = request.user
    today = timezone.now().date()
    
    # Filter by role - strict access control
    if user.is_doctor:
        # Doctors see ONLY their own appointments
        appointments = Appointment.objects.filter(doctor=user)
    elif user.is_receptionist or user.is_admin:
        # Receptionists and admins see all appointments
        appointments = Appointment.objects.all()
    elif user.is_nurse:
        # Nurses see only active appointments for today and future
        appointments = Appointment.objects.filter(
            Q(date__gte=today) & 
            Q(status__in=[Appointment.SCHEDULED, Appointment.CONFIRMED])
        )
    elif user.is_pharmacist:
        # Pharmacists only see completed appointments (for medication dispensing)
        appointments = Appointment.objects.filter(status=Appointment.COMPLETED)
    else:
        # Unauthorized roles shouldn't see any appointments
        messages.error(request, "You don't have permission to view appointments.")
        return redirect('dashboard')
    
    # Handle search and filters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    doctor_filter = request.GET.get('doctor', '')
    
    if search_query:
        appointments = appointments.filter(
            Q(patient__first_name__icontains=search_query) |
            Q(patient__last_name__icontains=search_query) |
            Q(patient__patient_id__icontains=search_query)
        )
    
    if status_filter:
        appointments = appointments.filter(status=status_filter)
        
    if date_filter:
        try:
            filter_date = datetime.datetime.strptime(date_filter, "%Y-%m-%d").date()
            appointments = appointments.filter(date=filter_date)
        except ValueError:
            pass
    
    # Only allow doctor filtering for admin and receptionist roles
    if doctor_filter and doctor_filter.isdigit() and (user.is_admin or user.is_receptionist):
        appointments = appointments.filter(doctor_id=int(doctor_filter))
    
    # Default ordering
    appointments = appointments.order_by('date', 'start_time')
    
    context = {
        'appointments': appointments,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'doctor_filter': doctor_filter,
        'today': today,
        'status_choices': Appointment.STATUS_CHOICES,
        'doctors': User.objects.filter(role=User.DOCTOR),
        'user_role': user.role, # Add user role to context for template-level access control
    }
    
    return render(request, 'appointment/appointment_list.html', context)


@login_required
def book_appointment(request):
    """View for booking new appointments"""
    if request.method == 'POST':
        print(f"POST data received: {request.POST}")
        form = AppointmentForm(request.POST, user=request.user)
        
        if form.is_valid():
            try:
                appointment = form.save(commit=False)
                appointment.status = Appointment.SCHEDULED
                appointment.created_by = request.user
                
                # Ensure all required fields are set
                if not appointment.start_time or not appointment.end_time:
                    time_slot = request.POST.get('time_slot', '')
                    if time_slot:
                        try:
                            start, end = time_slot.split(',')
                            appointment.start_time = datetime.datetime.strptime(start, '%H:%M').time()
                            appointment.end_time = datetime.datetime.strptime(end, '%H:%M').time()
                            print(f"Setting times from time_slot field: {start} - {end}")
                        except (ValueError, IndexError) as e:
                            print(f"Error parsing time_slot: {e}")
                            messages.error(request, f"Invalid time slot format: {time_slot}")
                            return redirect('book_appointment')
                
                # Set appointment type to EMERGENCY if is_emergency is checked
                if form.cleaned_data.get('is_emergency'):
                    appointment.appointment_type = Appointment.EMERGENCY
                    print("Setting appointment type to EMERGENCY")
                
                # Final verification before saving
                if not appointment.start_time or not appointment.end_time:
                    print("Still missing start or end time after processing")
                    messages.error(request, "Please select a time slot for this appointment")
                    return render(request, 'appointment/book_appointment.html', {
                        'form': form,
                        'slot_form': TimeSlotForm()
                    })
                
                print(f"Saving appointment: Patient={appointment.patient}, Doctor={appointment.doctor}, "
                      f"Date={appointment.date}, Time={appointment.start_time}-{appointment.end_time}")
                
                try:
                    # Save without validation first to troubleshoot
                    appointment.save()
                    # Success message
                    patient_name = appointment.patient.full_name
                    doctor_name = appointment.doctor.get_full_name()
                    emergency_text = " (EMERGENCY)" if appointment.is_emergency else ""
                    message = f"Appointment{emergency_text} scheduled successfully for {patient_name} with Dr. {doctor_name} on {appointment.date}"
                    messages.success(request, message)
                    
                    return redirect('appointment_list')
                except ValidationError as e:
                    print(f"Validation error while saving: {e}")
                    # If there's a validation error about doctor availability but this isn't an emergency,
                    # offer to make it an emergency appointment
                    error_msg = str(e)
                    if "Doctor is not available" in error_msg and not appointment.is_emergency:
                        form.data = form.data.copy()  # Make a mutable copy
                        form.data['is_emergency'] = True
                        messages.warning(request, 
                            "Doctor is not available during this time slot. "
                            "You can mark this as an emergency appointment to bypass availability restrictions.")
                        return render(request, 'appointment/book_appointment.html', {
                            'form': form,
                            'slot_form': TimeSlotForm()
                        })
                    messages.error(request, f"Validation error: {error_msg}")
            except ValidationError as e:
                print(f"Validation error: {e}")
                messages.error(request, f"Validation error: {str(e)}")
            except Exception as e:
                print(f"Error saving appointment: {e}")
                import traceback
                traceback.print_exc()
                messages.error(request, f"Error scheduling appointment: {str(e)}")
        else:
            print(f"Form errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        # Initialize with patient ID from query string if present
        initial_data = {}
        patient_id = request.GET.get('patient_id')
        if patient_id:
            try:
                patient = Patient.objects.get(id=patient_id)
                initial_data['patient'] = patient
                print(f"Pre-selected patient: {patient.full_name}")
            except Patient.DoesNotExist:
                print(f"Patient with ID {patient_id} not found")
                pass
        
        form = AppointmentForm(initial=initial_data, user=request.user)
        
        # Make sure all required fields are present
        for field_name in ['date', 'start_time', 'end_time', 'doctor', 'patient', 'appointment_type', 'reason']:
            if field_name not in form.fields:
                print(f"Missing required field in form: {field_name}")
                messages.error(request, f"Form missing required field: {field_name}")
    
    # Time slot selection form
    slot_form = TimeSlotForm()
    
    context = {
        'form': form,
        'slot_form': slot_form,
    }
    
    return render(request, 'appointment/book_appointment.html', context)


@login_required
def get_available_slots(request):
    """AJAX view to get available time slots for a doctor on a specific date, accounting for leave"""
    if request.method == 'GET':
        doctor_id = request.GET.get('doctor_id')
        date_str = request.GET.get('date')
        is_emergency = request.GET.get('is_emergency', 'false').lower() == 'true'
        
        print(f"get_available_slots called with doctor_id={doctor_id}, date={date_str}, is_emergency={is_emergency}")
        
        if not doctor_id or not date_str:
            print(f"Missing parameters: doctor_id={doctor_id}, date={date_str}")
            return JsonResponse({'error': 'Missing parameters'}, status=400)
        
        try:
            doctor = User.objects.get(id=doctor_id)
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            
            print(f"Found doctor: {doctor.get_full_name()}, for date: {date}")
            
            # For emergency cases, provide 24/7 availability
            if is_emergency:
                # Full 24-hour availability for emergencies
                start_time = datetime.time(0, 0)  # 12 AM
                end_time = datetime.time(23, 59)  # 11:59 PM
                
                # Short time slots for emergencies (15 min)
                available_slots = []
                slot_start = datetime.datetime.combine(date, start_time)
                end_datetime = datetime.datetime.combine(date, end_time)
                
                # Get existing appointments for this doctor on this date
                existing_appointments = Appointment.objects.filter(
                    doctor=doctor,
                    date=date,
                    status__in=[Appointment.SCHEDULED, Appointment.CONFIRMED]
                )
                
                print(f"Emergency slot search. Found {existing_appointments.count()} existing appointments.")
                
                while slot_start < end_datetime:
                    slot_end = slot_start + datetime.timedelta(minutes=15)
                    if slot_end > end_datetime:
                        slot_end = end_datetime
                    
                    # Check if this slot overlaps with existing appointments
                    is_available = True
                    for appt in existing_appointments:
                        appt_start = datetime.datetime.combine(date, appt.start_time)
                        appt_end = datetime.datetime.combine(date, appt.end_time)
                        
                        if slot_start < appt_end and slot_end > appt_start:
                            is_available = False
                            break
                    
                    if is_available:
                        available_slots.append({
                            'start': slot_start.strftime('%H:%M'),
                            'end': slot_end.strftime('%H:%M'),
                            'display': f"{slot_start.strftime('%H:%M')} - {slot_end.strftime('%H:%M')} (Emergency)"
                        })
                    
                    slot_start = slot_end
                
                print(f"Found {len(available_slots)} available emergency slots")
                
                # Always return at least one slot for emergency cases
                if not available_slots:
                    now = timezone.now()
                    if date == now.date():
                        current_hour = now.hour
                        current_minute = (now.minute // 15) * 15  # Round to nearest 15 min
                        
                        emergency_start = datetime.time(current_hour, current_minute)
                        emergency_end = (datetime.datetime.combine(date, emergency_start) + 
                                      datetime.timedelta(minutes=15)).time()
                        
                        # Add an emergency slot at the current time
                        available_slots.append({
                            'start': emergency_start.strftime('%H:%M'),
                            'end': emergency_end.strftime('%H:%M'),
                            'display': f"{emergency_start.strftime('%H:%M')} - {emergency_end.strftime('%H:%M')} (Emergency)"
                        })
                        print("Added emergency slot for current time")
                
                return JsonResponse({
                    'slots': available_slots,
                    'message': 'Emergency appointments are available 24/7'
                })
            
            # For regular appointments, use standard hospital hours
            # Default availability hours (8 AM to 10 PM)
            start_time = datetime.time(8, 0)
            end_time = datetime.time(22, 0)  # Updated from 20:00 (8 PM) to 22:00 (10 PM)
            
            # Check if doctor is on approved leave for this date
            doctor_leave = DoctorLeaveRequest.objects.filter(
                doctor=doctor,
                status=DoctorLeaveRequest.APPROVED,
                start_date__lte=date,
                end_date__gte=date
            ).first()
            
            # Get existing appointments for this doctor on this date
            existing_appointments = Appointment.objects.filter(
                doctor=doctor,
                date=date,
                status__in=[Appointment.SCHEDULED, Appointment.CONFIRMED]
            )
            
            print(f"Doctor on leave: {doctor_leave is not None}, Existing appointments: {existing_appointments.count()}")
            
            if doctor_leave:
                # Doctor is on approved leave for the entire day or part of the day
                leave_start = doctor_leave.start_time
                leave_end = doctor_leave.end_time
                
                # Generate available slots (using 30 min slots), accounting for leave time
                available_slots = []
                slot_start = datetime.datetime.combine(date, start_time)
                end_datetime = datetime.datetime.combine(date, end_time)
                
                while slot_start < end_datetime:
                    slot_end = slot_start + datetime.timedelta(minutes=30)
                    if slot_end > end_datetime:
                        slot_end = end_datetime
                    
                    # Skip slots that overlap with leave time
                    slot_start_time = slot_start.time()
                    slot_end_time = slot_end.time()
                    if (slot_start_time < leave_end and slot_end_time > leave_start):
                        slot_start = slot_end
                        continue
                    
                    # Check if this slot overlaps with existing appointments
                    is_available = True
                    for appt in existing_appointments:
                        appt_start = datetime.datetime.combine(date, appt.start_time)
                        appt_end = datetime.datetime.combine(date, appt.end_time)
                        
                        if slot_start < appt_end and slot_end > appt_start:
                            is_available = False
                            break
                    
                    if is_available:
                        available_slots.append({
                            'start': slot_start.strftime('%H:%M'),
                            'end': slot_end.strftime('%H:%M'),
                            'display': f"{slot_start.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}"
                        })
                    
                    slot_start = slot_end
                
                print(f"Found {len(available_slots)} available slots with doctor on leave")
                return JsonResponse({
                    'slots': available_slots,
                    'warning': 'Doctor is on partial leave for this day. Some time slots may not be available.'
                })
            else:
                # Check if doctor has availability defined
                doctor_has_slots = DoctorAvailability.objects.filter(doctor=doctor).exists()
                
                if doctor_has_slots:
                    # If doctor has availability slots, check if there's one for this day
                    day_of_week = date.weekday()
                    day_slots = DoctorAvailability.objects.filter(
                        doctor=doctor,
                        day_of_week=day_of_week
                    )
                    
                    if day_slots.exists():
                        # Use the doctor's defined availability for this day
                        available_slots = []
                        
                        for slot in day_slots:
                            slot_start = datetime.datetime.combine(date, slot.start_time)
                            slot_end = datetime.datetime.combine(date, slot.end_time)
                            
                            # Generate 30-minute intervals within this slot
                            current = slot_start
                            while current < slot_end:
                                interval_end = current + datetime.timedelta(minutes=30)
                                if interval_end > slot_end:
                                    interval_end = slot_end
                                
                                # Check if this interval overlaps with existing appointments
                                is_available = True
                                for appt in existing_appointments:
                                    appt_start = datetime.datetime.combine(date, appt.start_time)
                                    appt_end = datetime.datetime.combine(date, appt.end_time)
                                    
                                    if current < appt_end and interval_end > appt_start:
                                        is_available = False
                                        break
                                
                                if is_available:
                                    available_slots.append({
                                        'start': current.strftime('%H:%M'),
                                        'end': interval_end.strftime('%H:%M'),
                                        'display': f"{current.strftime('%H:%M')} - {interval_end.strftime('%H:%M')}"
                                    })
                                
                                current = interval_end
                        
                        print(f"Found {len(available_slots)} available slots based on doctor's specific availability")
                        return JsonResponse({'slots': available_slots})
                
                # No availability slots defined or none for this day - use standard hours
                # No leave - Generate available slots (using 30 min slots)
                available_slots = []
                slot_start = datetime.datetime.combine(date, start_time)
                end_datetime = datetime.datetime.combine(date, end_time)
                
                count_checked = 0
                count_overlapping = 0
                
                while slot_start < end_datetime:
                    slot_end = slot_start + datetime.timedelta(minutes=30)
                    if slot_end > end_datetime:
                        slot_end = end_datetime
                    
                    count_checked += 1
                    
                    # Check if this slot overlaps with existing appointments
                    is_available = True
                    for appt in existing_appointments:
                        appt_start = datetime.datetime.combine(date, appt.start_time)
                        appt_end = datetime.datetime.combine(date, appt.end_time)
                        
                        if slot_start < appt_end and slot_end > appt_start:
                            is_available = False
                            count_overlapping += 1
                            break
                    
                    if is_available:
                        available_slots.append({
                            'start': slot_start.strftime('%H:%M'),
                            'end': slot_end.strftime('%H:%M'),
                            'display': f"{slot_start.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}"
                        })
                    
                    slot_start = slot_end
                
                print(f"Checked {count_checked} slots, found {count_overlapping} overlapping with appointments")
                print(f"Found {len(available_slots)} available slots")
                
                # If no slots available for the current day, provide a message
                slots_response = {'slots': available_slots}
                if not available_slots:
                    slots_response['message'] = 'No time slots available for the selected date and doctor.'
                
                return JsonResponse(slots_response)
                
        except (User.DoesNotExist, ValueError) as e:
            print(f"Error finding doctor or parsing date: {str(e)}")
            return JsonResponse({'error': f'Invalid parameters: {str(e)}'}, status=400)
        except Exception as e:
            print(f"Unexpected error in get_available_slots: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': f'Error processing request: {str(e)}'}, status=500)
    
    print("Invalid request method")
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def appointment_detail(request, pk):
    """View for displaying appointment details"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Strict role-based permission checks
    user = request.user
    if user.is_doctor and user != appointment.doctor:
        messages.error(request, "You can only view your own appointments")
        return redirect('appointment_list')
    elif user.is_nurse and not (
        appointment.date >= timezone.now().date() and 
        appointment.status in [Appointment.SCHEDULED, Appointment.CONFIRMED]
    ):
        messages.error(request, "You can only view current and future active appointments")
        return redirect('appointment_list')
    elif user.is_pharmacist and appointment.status != Appointment.COMPLETED:
        messages.error(request, "You can only view completed appointments")
        return redirect('appointment_list')
    elif not (user.is_admin or user.is_receptionist or user == appointment.doctor or 
             user.is_nurse or user.is_pharmacist):
        messages.error(request, "You don't have permission to view this appointment")
        return redirect('dashboard')
    
    # Form for updating appointment status - only show to authorized roles
    show_status_form = user.is_admin or user.is_receptionist or user == appointment.doctor
    status_form = None
    if show_status_form:
        status_form = AppointmentStatusForm(initial={
            'status': appointment.status,
            'notes': ''  # Empty initial notes so old notes aren't resubmitted
        })
    
    context = {
        'appointment': appointment,
        'status_form': status_form,
        'show_status_form': show_status_form,
        'user_role': user.role,
    }
    
    return render(request, 'appointment/appointment_detail.html', context)


@login_required
def update_appointment_status(request, pk):
    """View for updating appointment status"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check if user has permission to update this appointment
    user = request.user
    if not (user.is_admin or user.is_receptionist or user == appointment.doctor):
        messages.error(request, "You don't have permission to update this appointment")
        return redirect('appointment_detail', pk=appointment.id)
    
    if request.method == 'POST':
        form = AppointmentStatusForm(request.POST)
        if form.is_valid():
            appointment.status = form.cleaned_data['status']
            
            # Update notes if provided
            if form.cleaned_data['notes']:
                if appointment.notes:
                    appointment.notes += f"\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {form.cleaned_data['notes']}"
                else:
                    appointment.notes = f"[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {form.cleaned_data['notes']}"
            
            appointment.save()
            messages.success(request, 'Appointment status updated successfully')
    
    return redirect('appointment_detail', pk=appointment.id)


@receptionist_required
def cancel_appointment(request, pk):
    """View for cancelling appointments"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        
        # Add cancellation note
        if reason:
            if appointment.notes:
                appointment.notes += f"\n[{timezone.now().strftime('%Y-%m-%d %H:%M')} - CANCELLED] {reason}"
            else:
                appointment.notes = f"[{timezone.now().strftime('%Y-%m-%d %H:%M')} - CANCELLED] {reason}"
        
        appointment.status = Appointment.CANCELLED
        appointment.save()
        
        messages.success(request, 'Appointment cancelled successfully')
        return redirect('appointment_list')
    
    return render(request, 'appointment/cancel_appointment.html', {'appointment': appointment})
