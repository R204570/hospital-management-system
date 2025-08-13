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
from .models import AppointmentInquiry, ContactInquiry, Blog, BlogSubscription, BlogComment
from .forms import BlogForm, BlogSubscriptionForm, BlogCommentForm
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

def blog(request):
    """Public blog listing page with search and filtering"""
    # If user is authenticated doctor, redirect to their blog management dashboard
    if request.user.is_authenticated and request.user.role == 'DOCTOR':
        return redirect('website:my_blogs')
    
    blogs = Blog.objects.filter(status='PUBLISHED').select_related('author').order_by('-published_at', '-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        blogs = blogs.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(excerpt__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    # Category filtering
    category = request.GET.get('category', '')
    if category:
        blogs = blogs.filter(category=category)
    
    # Author filtering
    author_id = request.GET.get('author', '')
    if author_id:
        try:
            blogs = blogs.filter(author_id=author_id)
        except (ValueError, TypeError):
            pass
    
    # Pagination
    paginator = Paginator(blogs, 6)  # 6 blogs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get recent blogs for sidebar
    recent_blogs = Blog.objects.filter(status='PUBLISHED').order_by('-published_at', '-created_at')[:3]
    
    # Get all doctors for filtering
    doctors = User.objects.filter(role='DOCTOR').order_by('first_name', 'last_name')
    
    # Category choices for filtering
    category_choices = Blog.CATEGORY_CHOICES
    
    context = {
        'blogs': page_obj,
        'recent_blogs': recent_blogs,
        'doctors': doctors,
        'category_choices': category_choices,
        'search_query': search_query,
        'selected_category': category,
        'selected_author': author_id,
    }
    return render(request, 'website/blog.html', context)

def blog_detail(request, slug):
    """Individual blog post detail page with comments"""
    blog_post = get_object_or_404(Blog, slug=slug, status='PUBLISHED')
    
    # Track unique views using session
    session_key = f'viewed_blog_{blog_post.id}'
    if not request.session.get(session_key, False):
        # Only increment if this user hasn't viewed this blog in this session
        blog_post.increment_views()
        request.session[session_key] = True
        # Set session expiry to 24 hours for view tracking
        request.session.set_expiry(86400)  # 24 hours in seconds
    
    # Get approved comments
    comments = blog_post.comments.filter(is_approved=True).order_by('created_at')
    
    # Handle AJAX requests
    if request.method == 'POST':
        # Handle comment submission
        if 'comment' in request.POST:
            comment_form = BlogCommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.blog_post = blog_post
                comment.is_approved = True  # Auto-approve comments for now
                comment.save()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Your comment has been posted successfully!'
                    })
                else:
                    messages.success(request, 'Your comment has been posted successfully!')
                    return redirect('website:blog_detail', slug=slug)
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Please check your input and try again.',
                        'errors': comment_form.errors
                    })
        
        # Handle subscription to this doctor's blogs
        elif 'subscribe' in request.POST:
            email = request.POST.get('email')
            if email:
                try:
                    subscription, created = BlogSubscription.objects.get_or_create(
                        email=email,
                        doctor=blog_post.author,
                        defaults={
                            'name': '',
                            'notification_frequency': 'IMMEDIATE',
                            'is_active': True
                        }
                    )
                    
                    if not created:
                        subscription.is_active = True
                        subscription.save()
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': f'Successfully subscribed to Dr. {blog_post.author.get_full_name()}!'
                        })
                    else:
                        messages.success(request, f'You have successfully subscribed to Dr. {blog_post.author.get_full_name()}\'s blog updates!')
                        return redirect('website:blog_detail', slug=slug)
                        
                except Exception as e:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'message': 'An error occurred. Please try again.'
                        })
                    else:
                        messages.error(request, 'You are already subscribed to this doctor\'s blog updates.')
                        return redirect('website:blog_detail', slug=slug)
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Email is required.'
                    })
    
    # Initialize forms for GET requests
    comment_form = BlogCommentForm()
    subscription_form = BlogSubscriptionForm()
    
    # Get recent blogs by the same author
    related_blogs = Blog.objects.filter(
        author=blog_post.author, 
        status='PUBLISHED'
    ).exclude(id=blog_post.id).order_by('-published_at')[:3]
    
    # Get recent blogs for sidebar
    recent_blogs = Blog.objects.filter(status='PUBLISHED').order_by('-published_at')[:3]
    
    context = {
        'blog_post': blog_post,
        'comments': comments,
        'comment_form': comment_form,
        'subscription_form': subscription_form,
        'related_blogs': related_blogs,
        'recent_blogs': recent_blogs,
    }
    return render(request, 'website/blog_detail.html', context)

@login_required
def create_blog(request):
    """Create new blog post - only for doctors"""
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Only doctors can create blog posts.')
        return redirect('website:blog')
    
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            blog_post = form.save(commit=False)
            blog_post.author = request.user
            
            # Set published_at if status is published
            if blog_post.status == 'PUBLISHED':
                blog_post.published_at = timezone.now()
            
            blog_post.save()
            messages.success(request, f'Blog post "{blog_post.title}" has been created successfully!')
            
            # Send notifications to subscribers if published
            if blog_post.status == 'PUBLISHED':
                send_blog_notifications(blog_post)
            
            return redirect('website:my_blogs')
        else:
            # Add form validation errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = BlogForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Create New Blog Post',
    }
    return render(request, 'website/blog_form.html', context)

@login_required
def edit_blog(request, slug):
    """Edit existing blog post - only author can edit"""
    blog_post = get_object_or_404(Blog, slug=slug)
    
    if request.user != blog_post.author:
        messages.error(request, 'You can only edit your own blog posts.')
        return redirect('website:blog_detail', slug=slug)
    
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES, instance=blog_post, user=request.user)
        if form.is_valid():
            was_draft = blog_post.status == 'DRAFT'
            blog_post = form.save()
            
            # Set published_at if changing from draft to published
            if was_draft and blog_post.status == 'PUBLISHED':
                blog_post.published_at = timezone.now()
                blog_post.save()
                # Send notifications to subscribers
                send_blog_notifications(blog_post)
            
            messages.success(request, f'Blog post "{blog_post.title}" has been updated successfully!')
            return redirect('website:my_blogs')
        else:
            # Add form validation errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = BlogForm(instance=blog_post, user=request.user)
    
    context = {
        'form': form,
        'blog_post': blog_post,
        'title': 'Edit Blog Post',
    }
    return render(request, 'website/blog_form.html', context)

@login_required
def delete_blog(request, slug):
    """Delete blog post - only author can delete"""
    blog_post = get_object_or_404(Blog, slug=slug)
    
    if request.user != blog_post.author:
        messages.error(request, 'You can only delete your own blog posts.')
        return redirect('website:blog_detail', slug=slug)
    
    if request.method == 'POST':
        title = blog_post.title
        blog_post.delete()
        messages.success(request, f'Blog post "{title}" has been deleted successfully!')
        return redirect('website:my_blogs')
    
    context = {
        'blog_post': blog_post,
    }
    return render(request, 'website/blog_confirm_delete.html', context)

@login_required
def my_blogs(request):
    """Doctor's personal blog management page"""
    if request.user.role != 'DOCTOR':
        messages.error(request, 'Only doctors can manage blog posts.')
        return redirect('website:blog')
    
    blogs = Blog.objects.filter(author=request.user).order_by('-created_at')
    
    # Statistics
    total_blogs = blogs.count()
    published_blogs = blogs.filter(status='PUBLISHED').count()
    draft_blogs = blogs.filter(status='DRAFT').count()
    total_views = sum(blog.views_count for blog in blogs)
    total_subscribers = BlogSubscription.objects.filter(doctor=request.user, is_active=True).count()
    
    context = {
        'blogs': blogs,
        'total_blogs': total_blogs,
        'published_blogs': published_blogs,
        'draft_blogs': draft_blogs,
        'total_views': total_views,
        'total_subscribers': total_subscribers,
    }
    return render(request, 'website/my_blogs.html', context)

@require_POST
def subscribe_to_doctor(request, doctor_id):
    """AJAX endpoint for subscribing to a doctor's blog"""
    doctor = get_object_or_404(User, id=doctor_id, role='DOCTOR')
    
    name = request.POST.get('name', '')
    email = request.POST.get('email', '')
    frequency = request.POST.get('frequency', 'IMMEDIATE')
    
    if not email:
        return JsonResponse({'success': False, 'message': 'Email is required.'})
    
    try:
        subscription, created = BlogSubscription.objects.get_or_create(
            email=email,
            doctor=doctor,
            defaults={
                'name': name,
                'notification_frequency': frequency,
                'is_active': True
            }
        )
        
        if created:
            message = f'Successfully subscribed to Dr. {doctor.get_full_name()}\'s blog updates!'
        else:
            subscription.is_active = True
            subscription.notification_frequency = frequency
            if name:
                subscription.name = name
            subscription.save()
            message = f'Your subscription to Dr. {doctor.get_full_name()}\'s blog has been updated!'
        
        return JsonResponse({'success': True, 'message': message})
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.'})

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

def doctors(request):
    return render(request, 'website/doctors.html')

def service(request):
    return render(request, 'website/service.html')

def login_view(request):
    # This will eventually point to the main Django login
    return render(request, 'users/login.html')

def appointment(request):
    return render(request, 'website/appointment.html')

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

def track_blog_view(request, slug):
    """Track blog view and redirect to blog detail page"""
    blog_post = get_object_or_404(Blog, slug=slug, status='PUBLISHED')
    
    # Track unique views using session
    session_key = f'viewed_blog_{blog_post.id}'
    if not request.session.get(session_key, False):
        # Only increment if this user hasn't viewed this blog in this session
        blog_post.increment_views()
        request.session[session_key] = True
        # Set session expiry to 24 hours for view tracking
        request.session.set_expiry(86400)  # 24 hours in seconds
    
    # Redirect to the actual blog detail page
    return redirect('website:blog_detail', slug=slug)

@require_POST
def delete_comment(request, comment_id):
    """AJAX endpoint for deleting a comment by the person who made it"""
    comment = get_object_or_404(BlogComment, id=comment_id)
    
    # Check if the request is from the same email that posted the comment
    requester_email = request.POST.get('email', '').strip().lower()
    comment_email = comment.email.strip().lower()
    
    if requester_email != comment_email:
        return JsonResponse({
            'success': False,
            'message': 'You can only delete your own comments.'
        })
    
    try:
        blog_slug = comment.blog_post.slug
        comment.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Comment deleted successfully!'
            })
        else:
            messages.success(request, 'Comment deleted successfully!')
            return redirect('website:blog_detail', slug=blog_slug)
            
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'An error occurred while deleting the comment.'
            })
        else:
            messages.error(request, 'An error occurred while deleting the comment.')
            return redirect('website:blog_detail', slug=comment.blog_post.slug)
