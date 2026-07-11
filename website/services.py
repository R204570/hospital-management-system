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


def send_blog_notifications(blog_post):
    """Send email notifications to subscribers when a new blog is published"""
    subscribers = BlogSubscription.objects.filter(
        doctor=blog_post.author,
        is_active=True,
        notification_frequency='IMMEDIATE'
    )
    
    for subscriber in subscribers:
        try:
            subject = f'New Blog Post by Dr. {blog_post.author.get_full_name()}: {blog_post.title}'
            message = f"""
Hello {subscriber.name or 'Reader'},

Dr. {blog_post.author.get_full_name()} has published a new blog post:

Title: {blog_post.title}
Category: {blog_post.get_category_display()}

{blog_post.excerpt}

Read the full post at: {settings.SITE_URL}/blog/{blog_post.slug}/

To unsubscribe from these notifications, please contact us.

Best regards,
Smart Care Hospital Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscriber.email],
                fail_silently=True
            )
            
            subscriber.last_notification_sent = timezone.now()
            subscriber.save()
            
        except Exception as e:
            continue  # Continue with other subscribers if one fails
