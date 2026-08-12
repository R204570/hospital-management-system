"""Production settings."""
import os

from .base import *  # noqa: F401,F403

DEBUG = False

# Comma-separated extra hosts can be supplied via ALLOWED_HOSTS env var.
ALLOWED_HOSTS = [
    'hospital-management-system-yhsp.onrender.com',
    '0.0.0.0.*',
]
ALLOWED_HOSTS += [
    h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()
]

CSRF_TRUSTED_ORIGINS = [
    'https://hospital-management-system-yhsp.onrender.com',
    '0.0.0.0.*',
]

# Basic production security hardening.
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
