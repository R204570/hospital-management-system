"""Profile views: view/update own profile, change password, diagnostics."""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone

from users import services
from users.forms import UserUpdateForm
from users.models import User


@login_required
def profile(request):
    """View for users to view and update their profile information."""
    user = request.user
    is_doctor = user.role == User.DOCTOR
    is_nurse = user.role == User.NURSE
    is_pharmacist = user.role == User.PHARMACIST

    edit_mode = request.GET.get('edit', 'false').lower() == 'true'

    if request.method == 'POST':
        # Clear-profile-picture button
        if 'clear_profile_picture' in request.POST:
            try:
                if services.clear_profile_picture(user):
                    messages.success(request, 'Profile picture removed successfully.')
            except Exception as e:
                print(f"Error removing profile picture: {str(e)}")
                messages.error(request, 'Error removing profile picture.')
            return redirect('profile')

        try:
            # Handle a cropped image payload, if any
            crop_error = services.apply_cropped_profile_picture(request)
            if crop_error:
                messages.error(request, crop_error)

            form = UserUpdateForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your profile has been updated successfully.')
                return redirect('profile')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                edit_mode = True
        except Exception as e:
            print(f"Error processing form: {str(e)}")
            messages.error(request, f"An error occurred: {str(e)}")
            edit_mode = True
    else:
        form = UserUpdateForm(instance=user)

    context = {
        'form': form,
        'is_doctor': is_doctor,
        'is_nurse': is_nurse,
        'is_pharmacist': is_pharmacist,
        'user': user,
        'media_url': settings.MEDIA_URL,
        'edit_mode': edit_mode,
    }
    return render(request, 'users/profile.html', context)


@login_required
def change_password(request):
    """View for users to change their password."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # keep the user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {'form': form})


@login_required
def test_profile_update(request):
    """Simple diagnostic view to verify the DB is writable for profile updates."""
    user = request.user
    if request.method == 'POST':
        try:
            old_first_name = user.first_name
            old_email = user.email

            test_first_name = f"Test-{timezone.now().strftime('%H%M%S')}"
            test_email = f"test-{timezone.now().strftime('%H%M%S')}@example.com"

            user.first_name = test_first_name
            user.email = test_email
            user.save()

            updated_user = request.user.__class__.objects.get(pk=user.pk)
            if updated_user.first_name == test_first_name and updated_user.email == test_email:
                user.first_name = old_first_name
                user.email = old_email
                user.save()
                return HttpResponse(
                    "<h1>Test Successful!</h1>"
                    "<p>Profile update test was successful. Database is writable.</p>"
                    "<p>Test values were applied and then reverted back.</p>"
                    f"<p><a href='{reverse_lazy('profile')}'>Return to profile</a></p>"
                )
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
    return render(request, 'users/test_profile_update.html')
