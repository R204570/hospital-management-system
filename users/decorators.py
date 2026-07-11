"""
Backwards-compatible shim.

The canonical role-based access decorators now live in ``core.decorators``.
This module re-exports them so existing imports (``from users.decorators
import ...``) keep working across the other apps.
"""
from core.decorators import (  # noqa: F401
    role_required,
    admin_required,
    doctor_required,
    nurse_required,
    receptionist_required,
    pharmacist_required,
    head_nurse_required,
)

__all__ = [
    'role_required',
    'admin_required',
    'doctor_required',
    'nurse_required',
    'receptionist_required',
    'pharmacist_required',
    'head_nurse_required',
]
