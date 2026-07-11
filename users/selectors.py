"""Read-only query helpers for the users app."""
from django.db.models import Q

from .models import User


def search_users(search='', role=''):
    """Return users filtered by a free-text ``search`` and/or ``role``."""
    users = User.objects.all().order_by('role', 'first_name')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    if role:
        users = users.filter(role=role)
    return users


def role_counts():
    """Return per-role user totals for the admin dashboard."""
    return {
        'total_users': User.objects.count(),
        'total_doctors': User.objects.filter(role=User.DOCTOR).count(),
        'total_nurses': User.objects.filter(role=User.NURSE).count(),
        'total_receptionists': User.objects.filter(role=User.RECEPTIONIST).count(),
        'total_pharmacists': User.objects.filter(role=User.PHARMACIST).count(),
    }
