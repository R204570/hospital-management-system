"""
Settings package selector.

Chooses the environment module based on the DJANGO_ENV environment variable:
  DJANGO_ENV=prod  -> hms_project.settings.prod
  anything else    -> hms_project.settings.dev  (default)

Keeping this as ``hms_project.settings`` means manage.py / wsgi.py / asgi.py
need no changes.
"""
import os

_env = os.environ.get('DJANGO_ENV', 'dev').lower()

if _env in ('prod', 'production'):
    from .prod import *  # noqa: F401,F403
else:
    from .dev import *  # noqa: F401,F403
