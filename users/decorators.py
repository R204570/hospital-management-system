from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.contrib import messages


def role_required(role):
    """
    Decorator for views that checks that the user has the specified role,
    redirecting to the login page if necessary.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if request.user.role != role:
                raise PermissionDenied
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def admin_required(function):
    """
    Decorator for views that checks that the user is an admin,
    redirecting to the homepage if necessary.
    """
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'ADMIN':
            return function(request, *args, **kwargs)
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    return wrapper


def doctor_required(function):
    """
    Decorator for views that checks that the user is a doctor,
    redirecting to the homepage if necessary.
    """
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'DOCTOR':
            return function(request, *args, **kwargs)
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    return wrapper


def nurse_required(function):
    """
    Decorator for views that checks that the user is a nurse,
    redirecting to the homepage if necessary.
    """
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'NURSE':
            return function(request, *args, **kwargs)
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    return wrapper


def receptionist_required(function):
    """
    Decorator for views that checks that the user is a receptionist,
    redirecting to the homepage if necessary.
    """
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'RECEPTIONIST':
            return function(request, *args, **kwargs)
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    return wrapper


def pharmacist_required(function):
    """
    Decorator for views that checks that the user is a pharmacist,
    redirecting to the homepage if necessary.
    """
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'PHARMACIST':
            return function(request, *args, **kwargs)
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard')
    return wrapper 