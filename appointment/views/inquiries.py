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
