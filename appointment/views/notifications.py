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
