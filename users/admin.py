from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .forms import UserRegistrationForm, AdminUserUpdateForm


class CustomUserAdmin(UserAdmin):
    """Custom admin interface for User model"""
    add_form = UserRegistrationForm
    form = AdminUserUpdateForm
    model = User
    
    # Fields displayed in user list
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    # Fields in the user detail form organized in fieldsets
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'address', 'profile_picture')}),
        ('Role & Doctor Info', {'fields': ('role', 'specialization', 'qualification')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Fields in the add user form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 
                      'role', 'phone_number', 'address', 'profile_picture', 'specialization', 
                      'qualification', 'is_active', 'is_staff')}
        ),
    )


# Register the custom admin interface
admin.site.register(User, CustomUserAdmin) 