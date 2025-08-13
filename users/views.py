from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone

from .forms import (UserRegistrationForm, UserUpdateForm, AdminUserUpdateForm, 
                    CustomAuthenticationForm, ForgotPasswordForm, 
                    OTPVerificationForm, SetNewPasswordForm)
from .models import User
from .decorators import admin_required
from .utils import generate_otp, send_otp_email, is_otp_valid

import os
from PIL import Image
from io import BytesIO
import base64
import binascii
import uuid
import logging

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    """Custom login view using the styled form"""
    template_name = 'users/login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Login'
        return context
    
    def form_valid(self, form):
        """Process valid form and add a welcome message with role information"""
        remember_me = form.cleaned_data.get('remember_me', False)
        if not remember_me:
            # Session expires when the user closes the browser
            self.request.session.set_expiry(0)
        
        response = super().form_valid(form)
        user = form.get_user()
        role_display = dict(User.ROLE_CHOICES).get(user.role, "User")
        
        # Add a custom welcome message with role information
        messages.success(
            self.request, 
            f"Welcome, {user.get_full_name() or user.username}! You are logged in as a {role_display}."
        )
        
        return response


def custom_logout(request):
    """Custom logout view that handles both GET and POST requests"""
    if request.user.is_authenticated:
        username = request.user.get_full_name() or request.user.username
        logout(request)
        messages.success(request, f"You have been successfully logged out. Thank you, {username}!")
    
    return redirect('login')


@login_required
def dashboard(request):
    """Main dashboard view after login, redirects based on user role"""
    user = request.user
    
    # For Django database users
    if user.role == 'ADMIN':
        return redirect('admin_dashboard')
    elif user.role == 'DOCTOR':
        return redirect('doctor_dashboard')
    elif user.role == 'NURSE':
        return redirect('nurse_dashboard')
    elif user.role == 'RECEPTIONIST':
        return redirect('receptionist_dashboard')
    elif user.role == 'PHARMACIST':
        return redirect('pharmacy_dashboard')
    else:
        return redirect('login')


@login_required
def profile(request):
    """View for users to view and update their profile information"""
    user = request.user
    is_doctor = user.role == User.DOCTOR
    is_nurse = user.role == User.NURSE
    is_pharmacist = user.role == User.PHARMACIST
    
    # Check if we're in edit mode
    edit_mode = request.GET.get('edit', 'false').lower() == 'true'
    
    if request.method == 'POST':
        # Check if the clear button for profile picture was pressed
        if 'clear_profile_picture' in request.POST:
            # If user had a profile picture, delete it
            if user.profile_picture:
                try:
                    # Store path for later deletion
                    if hasattr(user.profile_picture, 'path') and os.path.exists(user.profile_picture.path):
                        old_path = user.profile_picture.path
                        # Clear the profile picture
                        user.profile_picture = None
                        user.save()
                        # Delete the old file
                        os.remove(old_path)
                        messages.success(request, 'Profile picture removed successfully.')
                except Exception as e:
                    print(f"Error removing profile picture: {str(e)}")
                    messages.error(request, 'Error removing profile picture.')
            return redirect('profile')
        
        # Processing the main form submission
        print("POST data received:", request.POST)
        print("FILES received:", request.FILES)
        
        # Process the form submission
        try:
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
            
            # Simple approach - create form with all data
            form = UserUpdateForm(request.POST, request.FILES, instance=user)
            
            # Check form validity
            if form.is_valid():
                print("Form is valid - saving profile updates")
                
                # Save the form
                form.save()
                
                messages.success(request, 'Your profile has been updated successfully.')
                return redirect('profile')
            else:
                print("Form is invalid. Errors:", form.errors)
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                
                # Stay in edit mode if there are errors
                edit_mode = True
        except Exception as e:
            print(f"Error processing form: {str(e)}")
            messages.error(request, f"An error occurred: {str(e)}")
            edit_mode = True
    else:
        form = UserUpdateForm(instance=user)
    
    # Include user object in context to access profile_picture directly in template
    context = {
        'form': form,
        'is_doctor': is_doctor,
        'is_nurse': is_nurse,
        'is_pharmacist': is_pharmacist,
        'user': user,
        'media_url': settings.MEDIA_URL,
        'edit_mode': edit_mode
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def change_password(request):
    """View for users to change their password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Update the session to prevent logging out
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'users/change_password.html', {'form': form})


@admin_required
def admin_dashboard(request):
    """Dashboard view for administrators"""
    # Get summary counts for dashboard
    total_users = User.objects.count()
    total_doctors = User.objects.filter(role=User.DOCTOR).count()
    total_nurses = User.objects.filter(role=User.NURSE).count()
    total_receptionists = User.objects.filter(role=User.RECEPTIONIST).count()
    total_pharmacists = User.objects.filter(role=User.PHARMACIST).count()
    
    context = {
        'total_users': total_users,
        'total_doctors': total_doctors,
        'total_nurses': total_nurses,
        'total_receptionists': total_receptionists,
        'total_pharmacists': total_pharmacists,
    }
    
    return render(request, 'users/admin_dashboard.html', context)


@admin_required
def user_list(request):
    """View for administrators to see all users"""
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    users = User.objects.all().order_by('role', 'first_name')
    
    # Apply filters if provided
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) | 
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query) | 
            Q(email__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    context = {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter,
        'role_choices': User.ROLE_CHOICES,
    }
    
    return render(request, 'users/user_list.html', context)


@admin_required
def create_user(request):
    """View for administrators to create new users"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            # Set is_staff for admin users
            if user.role == User.ADMIN:
                user.is_staff = True
            user.save()
            messages.success(request, f'Account created for {user.username}!')
            return redirect('user_list')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/create_user.html', {'form': form})


@admin_required
def update_user(request, user_id):
    """View for administrators to update existing users"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = AdminUserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            updated_user = form.save(commit=False)
            # Update is_staff status based on role
            if updated_user.role == User.ADMIN:
                updated_user.is_staff = True
            updated_user.save()
            messages.success(request, f'Account updated for {updated_user.username}!')
            return redirect('user_list')
    else:
        form = AdminUserUpdateForm(instance=user)
    
    return render(request, 'users/update_user.html', {'form': form, 'user': user})


@csrf_exempt
def mongo_login(request):
    """
    Simple login view for testing MongoDB authentication
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return JsonResponse({
                'status': 'success',
                'message': f'Logged in as {username}',
                'user_role': user.role,
                'user_id': user.id
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid username or password'
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Only POST method is allowed'
    }, status=405)


def mongo_login_test(request):
    """
    View to serve the MongoDB login test page
    """
    return render(request, 'mongo_login_test.html')


def forgot_password(request):
    """View for initiating password reset"""
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            employee_id = form.cleaned_data['employee_id']
            email = form.cleaned_data['email']
            
            # Try to find user with license number or username
            user = None
            
            # Check all license number fields
            users = User.objects.filter(email=email)
            for u in users:
                if (u.doctor_license_number == employee_id or 
                    u.nurse_license_number == employee_id or 
                    u.pharmacist_license_number == employee_id or 
                    u.username == employee_id):
                    user = u
                    break
            
            if user:
                # Generate OTP and save to session
                otp = generate_otp()
                request.session['reset_otp'] = {
                    'otp': otp,
                    'user_id': user.id,
                    'created_at': timezone.now().isoformat()
                }
                
                # Send OTP via email
                if send_otp_email(user, otp):
                    messages.success(request, f"OTP sent to {email}. Please check your email.")
                    return redirect('verify_otp')
                else:
                    messages.error(request, "Failed to send OTP. Please try again.")
            else:
                messages.error(request, "No user found with the provided credentials.")
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'users/forgot_password.html', {'form': form})


def verify_otp(request):
    """View for OTP verification"""
    if 'reset_otp' not in request.session:
        messages.error(request, "Password reset session expired. Please try again.")
        return redirect('forgot_password')
    
    # Check session timeout (5 minutes)
    reset_data = request.session['reset_otp']
    created_at = timezone.datetime.fromisoformat(reset_data.get('created_at'))
    session_timeout = 3  # minutes
    
    if (timezone.now() - created_at) > timezone.timedelta(minutes=session_timeout):
        if 'reset_otp' in request.session:
            del request.session['reset_otp']
        if 'otp_verified' in request.session:
            del request.session['otp_verified']
        messages.error(request, "Your session has expired due to inactivity. Please try again.")
        return redirect('login')
    
    # Handle OTP resend
    if 'resend_otp' in request.GET:
        # Check if we can resend OTP (only after 2 minutes from last send)
        time_since_last_otp = timezone.now() - created_at
        
        if time_since_last_otp < timezone.timedelta(minutes=2):
            wait_seconds = 120 - time_since_last_otp.seconds
            messages.error(request, f"Please wait {wait_seconds} seconds before requesting a new OTP.")
            return redirect('verify_otp')
        
        # Generate new OTP
        user_id = reset_data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            new_otp = generate_otp()
            
            # Update session with new OTP
            request.session['reset_otp'] = {
                'otp': new_otp,
                'user_id': user.id,
                'created_at': timezone.now().isoformat()
            }
            
            # Send new OTP
            if send_otp_email(user, new_otp):
                messages.success(request, f"New OTP sent to your email. Please check your inbox.")
            else:
                messages.error(request, "Failed to send OTP. Please try again.")
        except User.DoesNotExist:
            messages.error(request, "User not found. Please try again.")
            return redirect('forgot_password')
        
        return redirect('verify_otp')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            user_otp = form.cleaned_data['otp']
            
            # Get stored OTP data
            stored_otp = reset_data.get('otp')
            user_id = reset_data.get('user_id')
            
            # Validate OTP
            if is_otp_valid(user_otp, stored_otp, created_at):
                # Mark OTP as verified and update timestamp to track session activity
                request.session['otp_verified'] = True
                request.session['last_activity'] = timezone.now().isoformat()
                return redirect('set_new_password')
            else:
                messages.error(request, "Invalid or expired OTP. Please try again.")
    else:
        form = OTPVerificationForm()
    
    # Calculate remaining time for the current OTP
    otp_expiry = created_at + timezone.timedelta(minutes=2)
    can_resend = timezone.now() >= (created_at + timezone.timedelta(minutes=2))
    
    context = {
        'form': form,
        'otp_expiry': otp_expiry,
        'can_resend': can_resend
    }
    
    return render(request, 'users/verify_otp.html', context)


def set_new_password(request):
    """View for setting new password after OTP verification"""
    if 'reset_otp' not in request.session or 'otp_verified' not in request.session:
        messages.error(request, "Password reset session expired. Please try again.")
        return redirect('forgot_password')
    
    # Check session timeout (5 minutes since last activity)
    if 'last_activity' in request.session:
        last_activity = timezone.datetime.fromisoformat(request.session['last_activity'])
        session_timeout = 3  # minutes
        
        if (timezone.now() - last_activity) > timezone.timedelta(minutes=session_timeout):
            # Clear session data
            if 'reset_otp' in request.session:
                del request.session['reset_otp']
            if 'otp_verified' in request.session:
                del request.session['otp_verified']
            if 'last_activity' in request.session:
                del request.session['last_activity']
                
            messages.error(request, "Your session has expired due to inactivity. Please try again.")
            return redirect('login')
    
    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            # Update last activity timestamp
            request.session['last_activity'] = timezone.now().isoformat()
            
            # Get user
            user_id = request.session['reset_otp'].get('user_id')
            try:
                user = User.objects.get(id=user_id)
                
                # Update password
                user.set_password(form.cleaned_data['new_password'])
                user.save()
                
                # Clear session
                if 'reset_otp' in request.session:
                    del request.session['reset_otp']
                if 'otp_verified' in request.session:
                    del request.session['otp_verified']
                if 'last_activity' in request.session:
                    del request.session['last_activity']
                
                messages.success(request, "Password reset successful. You can now login with your new password.")
                return redirect('forgot_password')
            except User.DoesNotExist:
                messages.error(request, "User not found. Please try again.")
                return redirect('forgot_password')
    else:
        form = SetNewPasswordForm()
        # Update last activity timestamp
        request.session['last_activity'] = timezone.now().isoformat()
    
    return render(request, 'users/set_new_password.html', {'form': form})


@login_required
def test_profile_update(request):
    """Simple test view to diagnose profile update issues"""
    user = request.user
    
    if request.method == 'POST':
        try:
            # Create a backup of current user data
            old_first_name = user.first_name
            old_email = user.email
            
            # Update simple fields to test DB connection
            test_first_name = f"Test-{timezone.now().strftime('%H%M%S')}"
            test_email = f"test-{timezone.now().strftime('%H%M%S')}@example.com"
            
            user.first_name = test_first_name
            user.email = test_email
            user.save()
            
            # Check if update was successful
            updated_user = request.user.__class__.objects.get(pk=user.pk)
            if updated_user.first_name == test_first_name and updated_user.email == test_email:
                # Success - restore original values
                user.first_name = old_first_name
                user.email = old_email
                user.save()
                return HttpResponse(
                    "<h1>Test Successful!</h1>"
                    "<p>Profile update test was successful. Database is writable.</p>"
                    "<p>Test values were applied and then reverted back.</p>"
                    f"<p><a href='{reverse_lazy('profile')}'>Return to profile</a></p>"
                )
            else:
                return HttpResponse(
                    "<h1>Test Failed!</h1>"
                    "<p>Values were not updated correctly.</p>"
                    f"<p>Expected: {test_first_name}, {test_email}</p>"
                    f"<p>Found: {updated_user.first_name}, {updated_user.email}</p>"
                    f"<p><a href='{reverse_lazy('profile')}'>Return to profile</a></p>"
                )
        except Exception as e:
            return HttpResponse(
                "<h1>Error during test!</h1>"
                f"<p>An error occurred: {str(e)}</p>"
                f"<p><a href='{reverse_lazy('profile')}'>Return to profile</a></p>"
            )
    else:
        return render(request, 'users/test_profile_update.html') 