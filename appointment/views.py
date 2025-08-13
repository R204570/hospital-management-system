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

from .models import Appointment, DoctorAvailability, DoctorLeaveRequest
from .forms import AppointmentForm, TimeSlotForm, DoctorAvailabilityForm, AppointmentStatusForm, DoctorLeaveRequestForm, LeaveRequestReviewForm
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


@login_required
def doctor_dashboard(request):
    """Dashboard view for doctors"""
    # Check if the user is a doctor
    if request.user.role != 'DOCTOR':
        # Redirect non-doctors to appropriate dashboard
        if request.user.role == 'RECEPTIONIST':
            return redirect('receptionist_dashboard')
        elif request.user.role == 'NURSE':
            return redirect('nurse_dashboard')
        elif request.user.role == 'ADMIN':
            return redirect('/admin/')
        else:
            return redirect('home')
    
    today = timezone.now().date()
    
    # Get today's appointments
    today_appointments = Appointment.objects.filter(
        doctor=request.user,
        date=today
    ).order_by('start_time')
    
    # Get upcoming appointments (limited to 10)
    upcoming_appointments = Appointment.objects.filter(
        doctor=request.user,
        date__gt=today
    ).order_by('date', 'start_time')[:10]
    
    # Get recent medical records created by this doctor
    recent_medical_records = []
    try:
        from patient.models import MedicalRecord
        recent_medical_records = MedicalRecord.objects.filter(
            doctor=request.user
        ).order_by('-report_date')[:5]
    except ImportError:
        pass
    
    # Get blog statistics
    published_blogs_count = 0
    try:
        from website.models import Blog
        published_blogs_count = Blog.objects.filter(
            author=request.user,
            status='PUBLISHED'
        ).count()
    except ImportError:
        pass
    
    context = {
        'today_appointments': today_appointments,
        'upcoming_appointments': upcoming_appointments,
        'recent_medical_records': recent_medical_records,
        'todays_appointments': today_appointments,  # Alias for template compatibility
        'published_blogs_count': published_blogs_count,
    }
    
    return render(request, 'appointment/doctor_dashboard.html', context)


@login_required
def receptionist_dashboard(request):
    """Receptionist dashboard with inquiry notifications"""
    # Check user permissions - only receptionists and admins can access
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to access this page.")
        return redirect('login')
    
    if not (request.user.is_receptionist or request.user.is_admin):
        messages.error(request, f"Access denied. Only receptionists and administrators can access this dashboard. Your role: {request.user.get_role_display()}")
        return redirect('dashboard')
    
    try:
        # Get all pending appointments
        pending_appointments_count = Appointment.objects.filter(status='SCHEDULED').count()
    
        # Get today's appointments  
        today = timezone.now().date()
        today_appointments = Appointment.objects.filter(
            date=today,
            status='SCHEDULED'
        ).order_by('start_time')[:10]  # Get actual appointment objects, not count
        
        # Get recent appointments (last 7 days)
        from datetime import timedelta
        week_ago = today - timedelta(days=7)
        recent_appointments = Appointment.objects.filter(
            date__gte=week_ago,
            date__lte=today
        ).order_by('-date', '-start_time')[:5]
        
        # Get inquiry statistics
        pending_appointment_inquiries = AppointmentInquiry.objects.filter(
            status='PENDING',
            notification_seen=False
        ).count()
        
        pending_contact_inquiries = ContactInquiry.objects.filter(
            status='PENDING',
            notification_seen=False
        ).count()
        
        # Get unread email replies count
        from website.models import EmailReply
        unread_email_replies = EmailReply.objects.filter(
            is_seen_by_staff=False
        ).count()
        
        pending_inquiries_count = pending_appointment_inquiries + pending_contact_inquiries + unread_email_replies
        
        # Get recent inquiries for sidebar - combine both types
        recent_appointment_inquiries = AppointmentInquiry.objects.filter(
            status__in=['PENDING', 'CONTACTED']
        ).order_by('-created_at')[:3]
        
        recent_contact_inquiries = ContactInquiry.objects.filter(
            status__in=['PENDING', 'READ']
        ).order_by('-created_at')[:3]
        
        # Combine recent inquiries for display
        recent_inquiries = []
        for inquiry in recent_appointment_inquiries:
            inquiry.inquiry_type = 'appointment'
            recent_inquiries.append(inquiry)
        for inquiry in recent_contact_inquiries:
            inquiry.inquiry_type = 'contact'
            recent_inquiries.append(inquiry)
        
        # Sort combined inquiries by creation date
        recent_inquiries.sort(key=lambda x: x.created_at, reverse=True)
        recent_inquiries = recent_inquiries[:5]  # Keep only top 5
        
        # Additional dashboard stats
        available_doctors_count = User.objects.filter(role='DOCTOR', is_available=True).count()
        
        context = {
            'pending_appointments_count': pending_appointments_count,
            'today_appointments': today_appointments,
            'recent_appointments': recent_appointments,
            'pending_appointment_inquiries': pending_appointment_inquiries,
            'pending_contact_inquiries': pending_contact_inquiries,
            'unread_email_replies': unread_email_replies,
            'pending_inquiries_count': pending_inquiries_count,
            'recent_appointment_inquiries': recent_appointment_inquiries,
            'recent_contact_inquiries': recent_contact_inquiries,
            'recent_inquiries': recent_inquiries,
            'available_doctors_count': available_doctors_count,
        }
        
        return render(request, 'appointment/receptionist_dashboard.html', context)
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return render(request, 'appointment/receptionist_dashboard.html', {})


@nurse_required
def nurse_dashboard(request):
    """Dashboard view for nurses"""
    today = timezone.now().date()
    
    # Today's appointments
    today_appointments = Appointment.objects.filter(
        date=today
    ).order_by('start_time')
    
    # Count statistics
    today_appointments_count = today_appointments.count()
    
    # Get count of registered patients
    try:
        from patient.models import Patient, MedicalRecord
        patients_count = Patient.objects.count()
        records_count = MedicalRecord.objects.count()
    except ImportError:
        patients_count = 0
        records_count = 0
    
    # Count doctors
    doctors_count = User.objects.filter(role='DOCTOR').count()
    
    context = {
        'today_appointments': today_appointments,
        'today_appointments_count': today_appointments_count,
        'patients_count': patients_count,
        'doctors_count': doctors_count,
        'records_count': records_count,
    }
    
    return render(request, 'appointment/nurse_dashboard.html', context)


@pharmacist_required
def pharmacy_dashboard(request):
    """Dashboard view for pharmacists"""
    today = timezone.now().date()
    
    # Placeholder data for dashboard statistics
    context = {
        'today_prescriptions_count': 0,
        'medicines_count': 0,
        'pending_orders_count': 0,
        'low_stock_count': 0,
        'recent_prescriptions': []
    }
    
    return render(request, 'appointment/pharmacy_dashboard.html', context)


@doctor_required
def doctor_leave_request(request):
    """View for doctors to request leave"""
    doctor = request.user
    
    if request.method == 'POST':
        form = DoctorLeaveRequestForm(request.POST, doctor=doctor)
        if form.is_valid():
            try:
                leave_request = form.save()
                
                # Verify that the leave request was properly saved
                if leave_request.pk:
                    # Check if there are appointments during the leave period
                    has_conflicts = leave_request.has_conflicts
                    
                    if has_conflicts:
                        messages.warning(request, 'Your leave request has been submitted, but there are existing appointments that may need to be rescheduled if the leave is approved.')
                    else:
                        messages.success(request, 'Your leave request has been submitted and is pending approval.')
                        
                    return redirect('doctor_leave_history')
                else:
                    messages.error(request, 'There was a problem saving your leave request. Please try again.')
            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
                # Log the error for debugging
                logger = logging.getLogger(__name__)
                logger.error(f"Error saving leave request: {str(e)}", exc_info=True)
        else:
            # Show form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
    else:
        form = DoctorLeaveRequestForm(doctor=doctor)
    
    context = {
        'form': form,
    }
    
    return render(request, 'appointment/doctor_leave_request.html', context)


@doctor_required
def doctor_leave_history(request):
    """View for doctors to see their leave request history"""
    doctor = request.user
    
    # Get all leave requests for this doctor
    leave_requests = DoctorLeaveRequest.objects.filter(doctor=doctor).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        leave_requests = leave_requests.filter(status=status_filter)
    
    context = {
        'leave_requests': leave_requests,
        'status_filter': status_filter,
        'status_choices': DoctorLeaveRequest.STATUS_CHOICES,
    }
    
    return render(request, 'appointment/doctor_leave_history.html', context)


@doctor_required
def cancel_leave_request(request, pk):
    """View for doctors to cancel their pending leave requests"""
    leave_request = get_object_or_404(DoctorLeaveRequest, pk=pk, doctor=request.user)
    
    # Only pending requests can be cancelled
    if leave_request.status != DoctorLeaveRequest.PENDING:
        messages.error(request, 'Only pending leave requests can be cancelled.')
        return redirect('doctor_leave_history')
    
    if request.method == 'POST':
        leave_request.status = DoctorLeaveRequest.CANCELLED
        leave_request.save()
        messages.success(request, 'Leave request cancelled successfully.')
        return redirect('doctor_leave_history')
    
    return render(request, 'appointment/cancel_leave_request.html', {'leave_request': leave_request})


@admin_required
def admin_leave_requests(request):
    """View for admins to see all leave requests"""
    # Get all leave requests, newest first
    leave_requests = DoctorLeaveRequest.objects.all().order_by('-created_at')
    
    # For debugging, log the number of leave requests found
    print(f"Total leave requests found: {leave_requests.count()}")
    for lr in leave_requests:
        print(f"Leave request: {lr.pk}, Doctor: {lr.doctor.get_full_name()}, Status: {lr.status}, Times: {lr.start_time}-{lr.end_time}")
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        leave_requests = leave_requests.filter(status=status_filter)
    
    # Filter by doctor if provided
    doctor_filter = request.GET.get('doctor', '')
    if doctor_filter and doctor_filter.isdigit():
        leave_requests = leave_requests.filter(doctor_id=int(doctor_filter))
    
    # Make sure we have the right doctors
    doctors = User.objects.filter(role='DOCTOR')
    
    context = {
        'leave_requests': leave_requests,
        'status_filter': status_filter,
        'doctor_filter': doctor_filter,
        'status_choices': DoctorLeaveRequest.STATUS_CHOICES,
        'doctors': doctors,
    }
    
    return render(request, 'appointment/admin_leave_requests.html', context)


@admin_required
def review_leave_request(request, pk):
    """View for admins to review and approve/reject leave requests"""
    leave_request = get_object_or_404(DoctorLeaveRequest, pk=pk)
    
    # Check if this request is already processed
    if leave_request.status not in [DoctorLeaveRequest.PENDING]:
        messages.warning(request, 'This leave request has already been processed.')
        return redirect('admin_leave_requests')
    
    # Get conflicting appointments
    conflicting_appointments = leave_request.conflicting_appointments
    
    if request.method == 'POST':
        form = LeaveRequestReviewForm(request.POST, instance=leave_request, admin_user=request.user)
        if form.is_valid():
            leave_request = form.save()
            
            status_display = leave_request.get_status_display()
            messages.success(request, f'Leave request {status_display.lower()} successfully.')
            
            # If approved and there are conflicts, show warning
            if leave_request.status == DoctorLeaveRequest.APPROVED and conflicting_appointments:
                messages.warning(request, f'There are {conflicting_appointments.count()} appointments that conflict with this approved leave. Please take action to reschedule or cancel them.')
                
            return redirect('admin_leave_requests')
    else:
        form = LeaveRequestReviewForm(instance=leave_request, admin_user=request.user)
    
    context = {
        'form': form,
        'leave_request': leave_request,
        'conflicting_appointments': conflicting_appointments,
    }
    
    return render(request, 'appointment/review_leave_request.html', context)


@doctor_required
def manage_availability(request):
    if request.method == 'POST':
        form = DoctorAvailabilityForm(request.POST)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.doctor = request.user
            try:
                availability.save()
                messages.success(request, 'Availability added successfully.')
                return redirect('manage_availability')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = DoctorAvailabilityForm()
    
    # Get all availability slots for the doctor
    availabilities = DoctorAvailability.objects.filter(doctor=request.user)
    
    context = {
        'form': form,
        'availabilities': availabilities
    }
    
    return render(request, 'appointment/manage_availability.html', context)


@doctor_required
def delete_availability(request, pk):
    try:
        availability = DoctorAvailability.objects.get(pk=pk, doctor=request.user)
        availability.delete()
        messages.success(request, 'Availability slot deleted successfully.')
    except DoctorAvailability.DoesNotExist:
        messages.error(request, 'Availability slot not found.')
    
    return redirect('manage_availability') 


# Inquiry Management Views

@login_required
def inquiry_list(request):
    """List all inquiries with search and filter functionality"""
    # Simplified access - just check if user is logged in
    print(f"DEBUG - inquiry_list accessed by: {request.user.username} (role: {request.user.role})")
    
    # For now, let any logged-in user access this page to test
    # TODO: Add proper permission checking later
    try:
        inquiry_type = request.GET.get('type', 'all')  # all, appointment, contact
        status_filter = request.GET.get('status', '')
        search_query = request.GET.get('search', '')
        
        # Get appointment inquiries
        appointment_inquiries = AppointmentInquiry.objects.all()
        if status_filter:
            appointment_inquiries = appointment_inquiries.filter(status=status_filter)
        if search_query:
            appointment_inquiries = appointment_inquiries.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(department__icontains=search_query)
            )
        
        # Get contact inquiries
        contact_inquiries = ContactInquiry.objects.all()
        if status_filter:
            contact_inquiries = contact_inquiries.filter(status=status_filter)
        if search_query:
            contact_inquiries = contact_inquiries.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(subject__icontains=search_query)
            )
        
        context = {
            'appointment_inquiries': appointment_inquiries[:20],
            'contact_inquiries': contact_inquiries[:20],
            'inquiry_type': inquiry_type,
            'status_filter': status_filter,
            'search_query': search_query,
        }
        
        return render(request, 'appointment/inquiry_list.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading inquiries: {str(e)}')
        return render(request, 'appointment/inquiry_list.html', {})


@login_required
def appointment_inquiry_detail(request, inquiry_id):
    """View and manage appointment inquiry details"""
    print(f"DEBUG - appointment_inquiry_detail accessed by: {request.user.username} (role: {request.user.role})")
    
    try:
        inquiry = get_object_or_404(AppointmentInquiry, id=inquiry_id)
        
        # Mark notification as seen
        if not inquiry.notification_seen:
            inquiry.notification_seen = True
            inquiry.save()
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'update_status':
                new_status = request.POST.get('status')
                inquiry.status = new_status
                inquiry.assigned_to = request.user
                inquiry.save()
                messages.success(request, f'Inquiry status updated to {new_status}')
                
            elif action == 'add_note':
                note = request.POST.get('note')
                if note:
                    if inquiry.notes:
                        inquiry.notes += f"\n\n{timezone.now().strftime('%Y-%m-%d %H:%M')} - {request.user.get_full_name()}: {note}"
                    else:
                        inquiry.notes = f"{timezone.now().strftime('%Y-%m-%d %H:%M')} - {request.user.get_full_name()}: {note}"
                    inquiry.save()
                    messages.success(request, 'Note added successfully')
                    
            elif action == 'send_reply':
                reply_message = request.POST.get('reply_message')
                if reply_message:
                    try:
                        # Send email reply using HTML template
                        from django.template.loader import render_to_string
                        from django.core.mail import EmailMultiAlternatives
                        
                        # Context for the email template
                        context = {
                            'inquiry': inquiry,
                            'reply_message': reply_message,
                            'replied_by_name': request.user.get_full_name() or request.user.username,
                        }
                        
                        # Render the HTML email template
                        html_content = render_to_string('appointment/email_reply_template.html', context)
                        
                        # Create plain text version
                        text_content = f"""Dear {inquiry.name},

Thank you for contacting SmartCare Hospital. We have received your inquiry and are pleased to provide you with the following response:

Your Inquiry:
Subject: {inquiry.get_department_display()} Appointment Request
Message: {inquiry.message}

Our Response:
{reply_message}

If you have any additional questions or need further assistance, please don't hesitate to contact us. We're here to help!

Best regards,
{request.user.get_full_name() or request.user.username}
SmartCare Hospital Reception Team

Contact Information:
Email: smart.care.2025.01@gmail.com
Phone: +1 (555) 123-4567

This is an automated response from SmartCare Hospital. For urgent medical matters, please contact our emergency services immediately."""
                        
                        # Create and send the email
                        subject = f"Re: Your Appointment Inquiry - {inquiry.get_department_display()}"
                        from_email = settings.EMAIL_HOST_USER  # Uses smart.care.2025.01@gmail.com
                        to_email = [inquiry.email]
                        
                        email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
                        email.attach_alternative(html_content, "text/html")
                        email.send()
                        
                        # Update inquiry
                        inquiry.reply_message = reply_message
                        inquiry.replied_at = timezone.now()
                        inquiry.status = 'CONTACTED'
                        inquiry.assigned_to = request.user
                        inquiry.save()
                        
                        messages.success(request, f'✅ Reply sent successfully to {inquiry.email}!')
                        
                    except Exception as e:
                        messages.error(request, f'❌ Failed to send email: {str(e)}')
        
        # Get related email replies (limit to 20 for performance)
        from website.models import EmailReply
        total_replies = EmailReply.objects.filter(
            related_appointment_inquiry=inquiry
        ).count()
        
        email_replies = EmailReply.objects.filter(
            related_appointment_inquiry=inquiry
        ).order_by('email_received_at')[:20]
        
        context = {
            'inquiry': inquiry,
            'inquiry_type': 'appointment',
            'email_replies': email_replies,
            'total_replies_count': total_replies,
            'replies_limit_reached': total_replies > 20,
        }
        
        return render(request, 'appointment/inquiry_detail.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading inquiry: {str(e)}')
        return redirect('inquiry_list')


@login_required
def contact_inquiry_detail(request, inquiry_id):
    """View and manage contact inquiry details"""
    print(f"DEBUG - contact_inquiry_detail accessed by: {request.user.username} (role: {request.user.role})")
    
    try:
        inquiry = get_object_or_404(ContactInquiry, id=inquiry_id)
        
        # Mark notification as seen
        if not inquiry.notification_seen:
            inquiry.notification_seen = True
            inquiry.save()
        
        if request.method == 'POST':
            action = request.POST.get('action')
            
            if action == 'update_status':
                new_status = request.POST.get('status')
                inquiry.status = new_status
                inquiry.assigned_to = request.user
                inquiry.save()
                messages.success(request, f'Inquiry status updated to {new_status}')
                
            elif action == 'add_note':
                note = request.POST.get('note')
                if note:
                    if inquiry.admin_notes:
                        inquiry.admin_notes += f"\n\n{timezone.now().strftime('%Y-%m-%d %H:%M')} - {request.user.get_full_name()}: {note}"
                    else:
                        inquiry.admin_notes = f"{timezone.now().strftime('%Y-%m-%d %H:%M')} - {request.user.get_full_name()}: {note}"
                    inquiry.save()
                    messages.success(request, 'Note added successfully')
                    
            elif action == 'send_reply':
                reply_message = request.POST.get('reply_message')
                if reply_message:
                    try:
                        # Send email reply using HTML template
                        from django.template.loader import render_to_string
                        from django.core.mail import EmailMultiAlternatives
                        
                        # Context for the email template
                        context = {
                            'inquiry': inquiry,
                            'reply_message': reply_message,
                            'replied_by_name': request.user.get_full_name() or request.user.username,
                        }
                        
                        # Render the HTML email template
                        html_content = render_to_string('appointment/email_reply_template.html', context)
                        
                        # Create plain text version
                        text_content = f"""Dear {inquiry.name},

Thank you for contacting SmartCare Hospital. We have received your inquiry and are pleased to provide you with the following response:

Your Inquiry:
Subject: {inquiry.subject}
Message: {inquiry.message}

Our Response:
{reply_message}

If you have any additional questions or need further assistance, please don't hesitate to contact us. We're here to help!

Best regards,
{request.user.get_full_name() or request.user.username}
SmartCare Hospital Reception Team

Contact Information:
Email: smart.care.2025.01@gmail.com
Phone: +1 (555) 123-4567

This is an automated response from SmartCare Hospital. For urgent medical matters, please contact our emergency services immediately."""
                        
                        # Create and send the email
                        subject = f"Re: {inquiry.subject}"
                        from_email = settings.EMAIL_HOST_USER  # Uses smart.care.2025.01@gmail.com
                        to_email = [inquiry.email]
                        
                        email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
                        email.attach_alternative(html_content, "text/html")
                        email.send()
                        
                        # Update inquiry
                        inquiry.reply_message = reply_message
                        inquiry.replied_at = timezone.now()
                        inquiry.status = 'REPLIED'
                        inquiry.assigned_to = request.user
                        inquiry.save()
                        
                        messages.success(request, f'✅ Reply sent successfully to {inquiry.email}!')
                        
                    except Exception as e:
                        messages.error(request, f'❌ Failed to send email: {str(e)}')
        
        # Get related email replies (limit to 20 for performance)
        from website.models import EmailReply
        total_replies = EmailReply.objects.filter(
            related_contact_inquiry=inquiry
        ).count()
        
        email_replies = EmailReply.objects.filter(
            related_contact_inquiry=inquiry
        ).order_by('email_received_at')[:20]
        
        context = {
            'inquiry': inquiry,
            'inquiry_type': 'contact',
            'email_replies': email_replies,
            'total_replies_count': total_replies,
            'replies_limit_reached': total_replies > 20,
        }
        
        return render(request, 'appointment/inquiry_detail.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading inquiry: {str(e)}')
        return redirect('inquiry_list')


@login_required
def mark_inquiries_seen(request):
    """AJAX endpoint to mark all inquiries as seen"""
    # Use same permission pattern as inquiry views - just @login_required
    if request.method == 'POST':
        try:
            AppointmentInquiry.objects.filter(notification_seen=False).update(notification_seen=True)
            ContactInquiry.objects.filter(notification_seen=False).update(notification_seen=True)
            
            # Also mark email replies as seen
            from website.models import EmailReply
            EmailReply.objects.filter(is_seen_by_staff=False).update(is_seen_by_staff=True)
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def get_notifications(request):
    """API endpoint to get unread inquiry notifications"""
    print(f"DEBUG - get_notifications called by: {request.user.username} (role: {request.user.get_role_display()})")
    
    # Use same permission pattern as inquiry views - just @login_required
    
    try:
        # Get unread appointment inquiries
        appointment_inquiries = AppointmentInquiry.objects.filter(
            status='PENDING',
            notification_seen=False
        ).order_by('-created_at')[:5]
        
        # Get unread contact inquiries
        contact_inquiries = ContactInquiry.objects.filter(
            status='PENDING',
            notification_seen=False
        ).order_by('-created_at')[:5]
        
        # Get unread email replies (only those linked to inquiries)
        from website.models import EmailReply
        email_replies = EmailReply.objects.filter(
            is_seen_by_staff=False
        ).exclude(
            related_contact_inquiry__isnull=True,
            related_appointment_inquiry__isnull=True
        ).order_by('-email_received_at')[:5]
        
        # Prepare data for response
        inquiries = []
        
        for inquiry in appointment_inquiries:
            time_diff = timezone.now() - inquiry.created_at
            if time_diff.days > 0:
                time_ago = f"{time_diff.days} days ago"
            elif time_diff.seconds // 3600 > 0:
                time_ago = f"{time_diff.seconds // 3600} hours ago"
            else:
                time_ago = f"{(time_diff.seconds // 60)} minutes ago"
                
            inquiries.append({
                'id': inquiry.id,
                'name': inquiry.name,
                'department': inquiry.get_department_display(),
                'subject': inquiry.get_department_display(),
                'time_ago': time_ago,
                'inquiry_type': 'appointment'
            })
        
        for inquiry in contact_inquiries:
            time_diff = timezone.now() - inquiry.created_at
            if time_diff.days > 0:
                time_ago = f"{time_diff.days} days ago"
            elif time_diff.seconds // 3600 > 0:
                time_ago = f"{time_diff.seconds // 3600} hours ago"
            else:
                time_ago = f"{(time_diff.seconds // 60)} minutes ago"
                
            inquiries.append({
                'id': inquiry.id,
                'name': inquiry.name,
                'department': '',
                'subject': inquiry.subject,
                'time_ago': time_ago,
                'inquiry_type': 'contact'
            })
        
        # Add email replies to notifications (only matched replies)
        for reply in email_replies:
            time_diff = timezone.now() - reply.email_received_at
            if time_diff.days > 0:
                time_ago = f"{time_diff.days} days ago"
            elif time_diff.seconds // 3600 > 0:
                time_ago = f"{time_diff.seconds // 3600} hours ago"
            else:
                time_ago = f"{(time_diff.seconds // 60)} minutes ago"
            
            # Get related inquiry info - only show matched replies
            related_inquiry = reply.get_related_inquiry()
            if related_inquiry:
                inquiries.append({
                    'id': reply.id,
                    'name': f"📧 {reply.sender_name or reply.sender_email}",
                    'department': 'Email Reply',
                    'subject': f"Reply: {reply.subject[:50]}...",
                    'time_ago': time_ago,
                    'inquiry_type': 'email_reply',
                    'related_inquiry_id': related_inquiry.id,
                    'related_inquiry_type': reply.get_inquiry_type()
                })
            # Skip unmatched emails - don't show in notifications
        
        # Sort by creation time (most recent first) - keep original order since we already ordered by -created_at
        inquiries = inquiries[:10]  # Return only top 10 to include email replies
        
        total_unread = len(appointment_inquiries) + len(contact_inquiries) + len(email_replies)
        
        return JsonResponse({
            'unread_count': total_unread,
            'inquiries': inquiries
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required  
def mark_inquiry_seen(request):
    """Mark a specific inquiry as seen"""
    # Use same permission pattern as inquiry views - just @login_required
    if request.method == 'POST':
        try:
            inquiry_id = request.POST.get('inquiry_id')
            inquiry_type = request.POST.get('inquiry_type')
            
            if inquiry_type == 'appointment':
                inquiry = get_object_or_404(AppointmentInquiry, id=inquiry_id)
                inquiry.notification_seen = True
                inquiry.save()
            elif inquiry_type == 'contact':
                inquiry = get_object_or_404(ContactInquiry, id=inquiry_id)  
                inquiry.notification_seen = True
                inquiry.save()
            else:
                return JsonResponse({'error': 'Invalid inquiry type'}, status=400)
                
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def mark_email_reply_seen(request):
    """Mark an email reply as seen by staff"""
    print(f"DEBUG - mark_email_reply_seen called by: {request.user.username}")
    print(f"DEBUG - Request method: {request.method}")
    print(f"DEBUG - POST data: {request.POST}")
    
    # Use same permission pattern as inquiry views - just @login_required, no extra checks
    if request.method == 'POST':
        try:
            from website.models import EmailReply
            reply_id = request.POST.get('reply_id')
            print(f"DEBUG - Reply ID: {reply_id}")
            
            if not reply_id:
                return JsonResponse({'error': 'Missing reply_id parameter'}, status=400)
            
            reply = get_object_or_404(EmailReply, id=reply_id)
            print(f"DEBUG - Found reply: {reply.sender_email} - {reply.subject}")
            
            reply.is_seen_by_staff = True
            reply.save()
            
            print(f"DEBUG - Successfully marked reply as seen")
            return JsonResponse({'success': True})
            
        except Exception as e:
            print(f"DEBUG - Error: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405) 