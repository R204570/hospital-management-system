"""Forms package for the users app (split by feature).

Every view is re-exported so ``from . import views`` and
``users.forms.<name>`` keep working unchanged.
"""
from .auth import (
    CustomAuthenticationForm,
)
from .accounts import (
    UserRegistrationForm,
    UserUpdateForm,
    AdminUserUpdateForm,
)
from .password_reset import (
    ForgotPasswordForm,
    OTPVerificationForm,
    SetNewPasswordForm,
)

__all__ = [
    "CustomAuthenticationForm",
    "UserRegistrationForm",
    "UserUpdateForm",
    "AdminUserUpdateForm",
    "ForgotPasswordForm",
    "OTPVerificationForm",
    "SetNewPasswordForm",
]
