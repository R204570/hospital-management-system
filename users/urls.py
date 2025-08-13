from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    path('', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Password reset with OTP
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('set-new-password/', views.set_new_password, name='set_new_password'),
    
    # Dashboard redirector
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # User profile management
    path('profile/', views.profile, name='profile'),
    path('profile/test/', views.test_profile_update, name='test_profile_update'),
    path('password/', views.change_password, name='change_password'),
    
    # Admin user management - renamed admin to management to avoid conflicts with Django admin
    path('management/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('management/users/', views.user_list, name='user_list'),
    path('management/users/create/', views.create_user, name='create_user'),
    path('management/users/<int:user_id>/update/', views.update_user, name='update_user'),
] 