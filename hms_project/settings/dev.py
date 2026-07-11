"""Development settings."""
from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0']

CSRF_TRUSTED_ORIGINS = []
