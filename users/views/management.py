"""Admin user-management views: list, create, update staff accounts."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from users import selectors
from users.decorators import admin_required
from users.forms import AdminUserUpdateForm, UserRegistrationForm
from users.models import User


@admin_required
def user_list(request):
    """View for administrators to see all users."""
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')

    context = {
        'users': selectors.search_users(search=search_query, role=role_filter),
        'search_query': search_query,
        'role_filter': role_filter,
        'role_choices': User.ROLE_CHOICES,
    }
    return render(request, 'users/user_list.html', context)


@admin_required
def create_user(request):
    """View for administrators to create new users."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
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
    """View for administrators to update existing users."""
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = AdminUserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            updated_user = form.save(commit=False)
            if updated_user.role == User.ADMIN:
                updated_user.is_staff = True
            updated_user.save()
            messages.success(request, f'Account updated for {updated_user.username}!')
            return redirect('user_list')
    else:
        form = AdminUserUpdateForm(instance=user)
    return render(request, 'users/update_user.html', {'form': form, 'user': user})
