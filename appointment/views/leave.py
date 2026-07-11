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
