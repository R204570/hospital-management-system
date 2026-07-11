"""
Base settings shared across all environments.

Environment-specific overrides live in dev.py / prod.py, selected by the
DJANGO_ENV environment variable (see __init__.py). Defaults to development.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Project root (three levels up: settings/ -> hms_project/ -> repo root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from the project-root .env file (if present)
load_dotenv(BASE_DIR / '.env')

# SECURITY WARNING: keep the secret key used in production secret!
# Provided via the SECRET_KEY env var in production; dev fallback below.
SECRET_KEY = os.environ.get(
    'SECRET_KEY', 'django-insecure-hms-secret-key-change-in-production'
)

# DEBUG and ALLOWED_HOSTS are defined per-environment in dev.py / prod.py.

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',

    # Custom apps
    'core.apps.CoreConfig',
    'users.apps.UsersConfig',
    'patient.apps.PatientConfig',
    'appointment.apps.AppointmentConfig',
    'billing.apps.BillingConfig',
    'pharmacy.apps.PharmacyConfig',
    'website',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'users.middleware.RoleBasedAccessMiddleware',
]

ROOT_URLCONF = 'hms_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'hms_project.wsgi.application'

# Database - Only SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Ensure profile pictures can be uploaded
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
AUTH_USER_MODEL = 'users.User'
LOGIN_REDIRECT_URL = 'dashboard'
LOGIN_URL = 'login'
LOGOUT_REDIRECT_URL = 'login'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Email configuration for Gmail
# Credentials are read from the .env file (never commit them):
#   EMAIL_HOST         -> the Gmail address (maps to Django's EMAIL_HOST_USER)
#   EMAIL_APP_PASSKEY  -> the Gmail app password (maps to EMAIL_HOST_PASSWORD)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # SMTP server (not the account address)
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST', '')  # Gmail address from .env
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_APP_PASSKEY', '')  # App password from .env

# IMAP configuration for reading emails (same credentials)
IMAP_HOST = 'imap.gmail.com'
IMAP_PORT = 993
IMAP_USE_SSL = True
IMAP_USERNAME = EMAIL_HOST_USER
IMAP_PASSWORD = EMAIL_HOST_PASSWORD

# Session and cookie settings
SESSION_COOKIE_AGE = 172800  # 2 days in seconds for "Remember Me" functionality
