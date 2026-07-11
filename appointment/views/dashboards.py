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
