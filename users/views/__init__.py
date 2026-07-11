"""
Views package for the users app.

Split by feature into submodules; every public view is re-exported here so
that ``from . import views`` (in urls.py) and ``users.views.<name>`` keep
working exactly as before.
"""
from .auth import CustomLoginView, custom_logout, mongo_login, mongo_login_test
from .dashboard import admin_dashboard, dashboard
from .management import create_user, update_user, user_list
from .password_reset import forgot_password, set_new_password, verify_otp
from .profile import change_password, profile, test_profile_update

__all__ = [
    "CustomLoginView", "custom_logout", "mongo_login", "mongo_login_test",
    "dashboard", "admin_dashboard",
    "user_list", "create_user", "update_user",
    "forgot_password", "verify_otp", "set_new_password",
    "profile", "change_password", "test_profile_update",
]
