"""Authentication views: login, logout, and legacy MongoDB test endpoints."""
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from users.forms import CustomAuthenticationForm
from users.models import User


class CustomLoginView(LoginView):
    """Custom login view using the styled form."""
    template_name = 'users/login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Login'
        return context

    def form_valid(self, form):
        """Process valid form and add a welcome message with role information."""
        remember_me = form.cleaned_data.get('remember_me', False)
        if not remember_me:
            # Session expires when the user closes the browser
            self.request.session.set_expiry(0)

        response = super().form_valid(form)
        user = form.get_user()
        role_display = dict(User.ROLE_CHOICES).get(user.role, "User")

        messages.success(
            self.request,
            f"Welcome, {user.get_full_name() or user.username}! "
            f"You are logged in as a {role_display}."
        )
        return response


def custom_logout(request):
    """Custom logout view that handles both GET and POST requests."""
    if request.user.is_authenticated:
        username = request.user.get_full_name() or request.user.username
        logout(request)
        messages.success(request, f"You have been successfully logged out. Thank you, {username}!")
    return redirect('login')


@csrf_exempt
def mongo_login(request):
    """Simple login endpoint kept for legacy MongoDB auth testing."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({
                'status': 'success',
                'message': f'Logged in as {username}',
                'user_role': user.role,
                'user_id': user.id,
            })
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid username or password',
        }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Only POST method is allowed',
    }, status=405)


def mongo_login_test(request):
    """Serve the MongoDB login test page (legacy)."""
    return render(request, 'mongo_login_test.html')
