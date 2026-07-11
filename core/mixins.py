"""Reusable class-based-view mixins for role-based access."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict a CBV to users whose ``role`` is in ``allowed_roles``."""

    allowed_roles = ()

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.role in self.allowed_roles

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            return redirect('dashboard')
        return super().handle_no_permission()
