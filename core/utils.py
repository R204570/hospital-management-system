"""Shared helper utilities used across apps."""

# Map each staff role to its landing dashboard URL name.
ROLE_DASHBOARD_URLS = {
    'ADMIN': 'admin_dashboard',
    'DOCTOR': 'doctor_dashboard',
    'NURSE': 'nurse_dashboard',
    'RECEPTIONIST': 'receptionist_dashboard',
    'PHARMACIST': 'pharmacy_dashboard',
}


def dashboard_url_for_role(role):
    """Return the dashboard URL name for the given user role."""
    return ROLE_DASHBOARD_URLS.get(role, 'login')
