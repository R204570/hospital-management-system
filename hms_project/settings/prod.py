"""Production settings."""
import os

from .base import *  # noqa: F401,F403

DEBUG = False


def _csv_env(name):
    """Read a comma-separated environment variable into a list of entries."""
    return [item.strip() for item in os.environ.get(name, '').split(',') if item.strip()]


# Render publishes the service hostname as RENDER_EXTERNAL_HOSTNAME; the leading
# dot on '.onrender.com' matches any subdomain, which covers renamed services.
# Extra hosts can be supplied via the ALLOWED_HOSTS env var (comma-separated).
ALLOWED_HOSTS = ['.onrender.com']
if os.environ.get('RENDER_EXTERNAL_HOSTNAME'):
    ALLOWED_HOSTS.append(os.environ['RENDER_EXTERNAL_HOSTNAME'])
ALLOWED_HOSTS += _csv_env('ALLOWED_HOSTS')

# Every entry must include a scheme -- Django 4.0+ rejects bare hosts and '*'
# with system check 4_0.E001, which stops the app from booting at all.
CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']
if os.environ.get('RENDER_EXTERNAL_URL'):
    CSRF_TRUSTED_ORIGINS.append(os.environ['RENDER_EXTERNAL_URL'].rstrip('/'))
CSRF_TRUSTED_ORIGINS += _csv_env('CSRF_TRUSTED_ORIGINS')

# Render terminates TLS at its proxy and forwards the request over plain HTTP.
# Without this Django sees request.scheme == 'http' and rejects HTTPS form
# posts as CSRF origin mismatches.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# DEBUG = False stops Django serving /static/ itself, so WhiteNoise takes over.
# It has to sit directly after SecurityMiddleware.
MIDDLEWARE = MIDDLEWARE[:1] + ['whitenoise.middleware.WhiteNoiseMiddleware'] + MIDDLEWARE[1:]  # noqa: F405

# Fall back to the staticfiles finders (i.e. serve straight out of STATICFILES_DIRS
# and each app's static/ dir) so the site still gets its CSS when the host's build
# command has not run collectstatic. build.sh runs it, which is faster and adds
# compression, but this keeps a misconfigured build from shipping an unstyled site.
WHITENOISE_USE_FINDERS = True

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}

# Basic production security hardening.
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
