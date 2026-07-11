"""Dashboard views: post-login role redirector and the admin dashboard."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core.utils import dashboard_url_for_role
from users.analytics import hospital_analytics
from users.decorators import admin_required


@login_required
def dashboard(request):
    """Main dashboard view after login; redirects based on user role."""
    return redirect(dashboard_url_for_role(request.user.role))


@admin_required
def admin_dashboard(request):
    """Dashboard view for administrators with hospital-wide analytics."""
    return render(request, 'users/admin_dashboard.html', hospital_analytics())
