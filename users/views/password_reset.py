"""Password-reset flow: request OTP, verify OTP, set new password."""
from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone

from users.forms import ForgotPasswordForm, OTPVerificationForm, SetNewPasswordForm
from users.models import User
from users.utils import generate_otp, is_otp_valid, send_otp_email


def forgot_password(request):
    """View for initiating password reset."""
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            employee_id = form.cleaned_data['employee_id']
            email = form.cleaned_data['email']

            # Match the employee id against any of the license/username fields
            user = None
            for u in User.objects.filter(email=email):
                if (u.doctor_license_number == employee_id or
                        u.nurse_license_number == employee_id or
                        u.pharmacist_license_number == employee_id or
                        u.username == employee_id):
                    user = u
                    break

            if user:
                otp = generate_otp()
                request.session['reset_otp'] = {
                    'otp': otp,
                    'user_id': user.id,
                    'created_at': timezone.now().isoformat(),
                }
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
    """View for OTP verification."""
    if 'reset_otp' not in request.session:
        messages.error(request, "Password reset session expired. Please try again.")
        return redirect('forgot_password')

    reset_data = request.session['reset_otp']
    created_at = timezone.datetime.fromisoformat(reset_data.get('created_at'))
    session_timeout = 3  # minutes

    if (timezone.now() - created_at) > timezone.timedelta(minutes=session_timeout):
        request.session.pop('reset_otp', None)
        request.session.pop('otp_verified', None)
        messages.error(request, "Your session has expired due to inactivity. Please try again.")
        return redirect('login')

    # Handle OTP resend
    if 'resend_otp' in request.GET:
        time_since_last_otp = timezone.now() - created_at
        if time_since_last_otp < timezone.timedelta(minutes=2):
            wait_seconds = 120 - time_since_last_otp.seconds
            messages.error(request, f"Please wait {wait_seconds} seconds before requesting a new OTP.")
            return redirect('verify_otp')

        user_id = reset_data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            new_otp = generate_otp()
            request.session['reset_otp'] = {
                'otp': new_otp,
                'user_id': user.id,
                'created_at': timezone.now().isoformat(),
            }
            if send_otp_email(user, new_otp):
                messages.success(request, "New OTP sent to your email. Please check your inbox.")
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
            stored_otp = reset_data.get('otp')

            if is_otp_valid(user_otp, stored_otp, created_at):
                request.session['otp_verified'] = True
                request.session['last_activity'] = timezone.now().isoformat()
                return redirect('set_new_password')
            else:
                messages.error(request, "Invalid or expired OTP. Please try again.")
    else:
        form = OTPVerificationForm()

    otp_expiry = created_at + timezone.timedelta(minutes=2)
    can_resend = timezone.now() >= (created_at + timezone.timedelta(minutes=2))

    context = {
        'form': form,
        'otp_expiry': otp_expiry,
        'can_resend': can_resend,
    }
    return render(request, 'users/verify_otp.html', context)


def set_new_password(request):
    """View for setting a new password after OTP verification."""
    if 'reset_otp' not in request.session or 'otp_verified' not in request.session:
        messages.error(request, "Password reset session expired. Please try again.")
        return redirect('forgot_password')

    # Check session timeout since last activity
    if 'last_activity' in request.session:
        last_activity = timezone.datetime.fromisoformat(request.session['last_activity'])
        session_timeout = 3  # minutes
        if (timezone.now() - last_activity) > timezone.timedelta(minutes=session_timeout):
            request.session.pop('reset_otp', None)
            request.session.pop('otp_verified', None)
            request.session.pop('last_activity', None)
            messages.error(request, "Your session has expired due to inactivity. Please try again.")
            return redirect('login')

    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            request.session['last_activity'] = timezone.now().isoformat()
            user_id = request.session['reset_otp'].get('user_id')
            try:
                user = User.objects.get(id=user_id)
                user.set_password(form.cleaned_data['new_password'])
                user.save()

                request.session.pop('reset_otp', None)
                request.session.pop('otp_verified', None)
                request.session.pop('last_activity', None)

                messages.success(request, "Password reset successful. You can now login with your new password.")
                return redirect('forgot_password')
            except User.DoesNotExist:
                messages.error(request, "User not found. Please try again.")
                return redirect('forgot_password')
    else:
        form = SetNewPasswordForm()
        request.session['last_activity'] = timezone.now().isoformat()

    return render(request, 'users/set_new_password.html', {'form': form})
