"""
Role-based access decorators for function-based views.

Canonical home for the decorators previously defined in users/decorators.py.
"""
from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from core import constants


def role_required(role):
    """Require the authenticated user to have exactly ``role`` (else 403)."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            # Admins have access to every role-gated view
            if request.user.role not in (role, constants.ADMIN):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def _role_guard(role):
    """Build a decorator that redirects to the dashboard on the wrong role."""
    def decorator(function):
        @wraps(function)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.role in (role, constants.ADMIN):
                return function(request, *args, **kwargs)
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard')
        return wrapper
    return decorator


admin_required = _role_guard(constants.ADMIN)
doctor_required = _role_guard(constants.DOCTOR)
nurse_required = _role_guard(constants.NURSE)
receptionist_required = _role_guard(constants.RECEPTIONIST)
pharmacist_required = _role_guard(constants.PHARMACIST)


def head_nurse_required(function):
    """Allow only head nurses (nurse + is_head_nurse) and admins."""
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        u = request.user
        if u.is_authenticated and (
            u.role == constants.ADMIN
            or (u.role == constants.NURSE and getattr(u, 'is_head_nurse', False))
        ):
            return function(request, *args, **kwargs)
        messages.error(request, "You don't have permission to manage the hospital inventory.")
        return redirect('dashboard')
    return wrapper
