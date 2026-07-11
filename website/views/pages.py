from django.shortcuts import render, get_object_or_404, redirect
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from website.models import AppointmentInquiry, ContactInquiry, Blog, BlogSubscription, BlogComment
from website.forms import BlogForm, BlogSubscriptionForm, BlogCommentForm
from users.models import User
import os

# Create your views here.


def index(request):
    return render(request, 'website/index.html')


def about(request):
    return render(request, 'website/about.html')


def contact(request):
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Validate required fields
        if not all([name, email, phone, subject, message]):
            context = {
                'error_message': 'Please fill in all required fields.'
            }
            return render(request, 'website/contact.html', context)
        
        try:
            # Create the contact inquiry
            contact_inquiry = ContactInquiry(
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message
            )
            contact_inquiry.save()
            
            success_message = f'Your message has been sent successfully! We will contact you soon at {email}.'
            context = {
                'success_message': success_message
            }
            return render(request, 'website/contact.html', context)
            
        except Exception as e:
            context = {
                'error_message': 'There was an error sending your message. Please try again.'
            }
            return render(request, 'website/contact.html', context)
    
    return render(request, 'website/contact.html')


def doctors(request):
    return render(request, 'website/doctors.html')


def service(request):
    return render(request, 'website/service.html')


def login_view(request):
    # This will eventually point to the main Django login
    return render(request, 'users/login.html')


def appointment(request):
    # 'website/appointment.html' does not exist; the inquiry page is the booking form
    return redirect('website:appointment_inquiry')


def appointment_inquiry(request):
    # Get all doctors for the form
    from users.models import User
    doctors = User.objects.filter(role='DOCTOR').order_by('first_name', 'last_name')
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        department = request.POST.get('department')
        preferred_doctor_id = request.POST.get('preferred_doctor')
        message = request.POST.get('message')
        preferred_date = request.POST.get('preferred_date')
        
        # Validate required fields
        if not all([name, email, phone, department, message, preferred_date]):
            context = {
                'error_message': 'Please fill in all required fields.',
                'doctors': doctors
            }
            return render(request, 'website/appointment_inquiry.html', context)
        
        try:
            # Get preferred doctor if selected
            preferred_doctor = None
            if preferred_doctor_id:
                try:
                    preferred_doctor = User.objects.get(id=preferred_doctor_id, role='DOCTOR')
                except User.DoesNotExist:
                    preferred_doctor = None
            
            # Create the inquiry
            inquiry = AppointmentInquiry(
                name=name,
                email=email,
                phone=phone,
                department=department,
                preferred_doctor=preferred_doctor,
                message=message,
                preferred_date=preferred_date
            )
            
            # Handle file upload if present
            if 'health_records' in request.FILES:
                uploaded_file = request.FILES['health_records']
                
                # Validate file size (5MB limit)
                if uploaded_file.size > 5 * 1024 * 1024:  # 5MB in bytes
                    context = {
                        'error_message': 'File size must be less than 5MB. Please choose a smaller file.',
                        'doctors': doctors
                    }
                    return render(request, 'website/appointment_inquiry.html', context)
                
                # Validate file type
                allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                
                if file_extension not in allowed_extensions:
                    context = {
                        'error_message': 'Invalid file type. Please upload PDF, DOC, DOCX, JPG, or PNG files only.',
                        'doctors': doctors
                    }
                    return render(request, 'website/appointment_inquiry.html', context)
                
                # Assign the file to the inquiry
                inquiry.health_records = uploaded_file
            
            # Save the inquiry
            inquiry.save()
            
            success_message = f'Your appointment inquiry has been submitted successfully! We will contact you soon at {email}.'
            if inquiry.health_records:
                success_message += f' Your health record "{inquiry.health_records.name}" has been uploaded successfully.'
            
            context = {
                'success_message': success_message,
                'doctors': doctors
            }
            return render(request, 'website/appointment_inquiry.html', context)
            
        except Exception as e:
            context = {
                'error_message': 'There was an error submitting your inquiry. Please try again.',
                'doctors': doctors
            }
            return render(request, 'website/appointment_inquiry.html', context)
    
    context = {
        'doctors': doctors
    }
    return render(request, 'website/appointment_inquiry.html', context)
