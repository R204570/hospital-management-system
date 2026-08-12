"""
Settings package selector.

Chooses the environment module based on the DJANGO_ENV environment variable:
  DJANGO_ENV=prod  -> hms_project.settings.prod
  anything else    -> hms_project.settings.dev  (default)

When DJANGO_ENV is unset we fall back to prod on a hosting platform that
identifies itself (Render sets RENDER=true), so a forgotten env var cannot
silently boot a live deploy with development settings.

Keeping this as ``hms_project.settings`` means manage.py / wsgi.py / asgi.py
need no changes.
"""
import os

_env = os.environ.get('DJANGO_ENV', '').lower()

if not _env:
    _env = 'prod' if os.environ.get('RENDER') else 'dev'

if _env in ('prod', 'production'):
    from .prod import *  # noqa: F401,F403
else:
    from .dev import *  # noqa: F401,F403
