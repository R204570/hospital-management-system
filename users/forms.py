from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm, PasswordChangeForm
from django.utils.translation import gettext_lazy as _
from .models import User


class CustomAuthenticationForm(AuthenticationForm):
    """Custom authentication form with Bootstrap styling"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class UserRegistrationForm(UserCreationForm):
    """Form for creating new users by admin"""
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone_number', 
                 'address', 'profile_picture', 'qualification', 'years_of_experience',
                 # Doctor fields
                 'specialization', 'doctor_license_number', 'is_available',
                 # Nurse fields
                 'nurse_license_number', 'nursing_specialty',
                 # Pharmacist fields
                 'pharmacist_license_number', 'pharmacy_certification']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to all form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            
        # Set the choices for specialization
        self.fields['specialization'].widget = forms.Select(choices=User.SPECIALIZATION_CHOICES)
        self.fields['specialization'].widget.attrs['class'] = 'form-select'

        # Conditionally show role-specific fields
        doctor_fields = ['specialization', 'doctor_license_number', 'is_available']
        for field_name in doctor_fields:
            self.fields[field_name].widget.attrs['data-role-dependent'] = 'DOCTOR'

        nurse_fields = ['nurse_license_number', 'nursing_specialty']
        for field_name in nurse_fields:
            self.fields[field_name].widget.attrs['data-role-dependent'] = 'NURSE'

        pharmacist_fields = ['pharmacist_license_number', 'pharmacy_certification']
        for field_name in pharmacist_fields:
            self.fields[field_name].widget.attrs['data-role-dependent'] = 'PHARMACIST'


class UserUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 
                 'address', 'profile_picture', 'qualification', 'years_of_experience',
                 # Doctor fields
                 'specialization', 'doctor_license_number', 'is_available',
                 # Nurse fields
                 'nurse_license_number', 'nursing_specialty',
                 # Pharmacist fields
                 'pharmacist_license_number', 'pharmacy_certification']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            
        # Make username read-only since it shouldn't be changed easily
        self.fields['username'].widget.attrs['readonly'] = True
        
        # Set the choices for specialization
        self.fields['specialization'].widget = forms.Select(choices=User.SPECIALIZATION_CHOICES)
        self.fields['specialization'].widget.attrs['class'] = 'form-select'
        
        # Set checkbox widget for is_available
        self.fields['is_available'].widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})
        
        # Ensure the profile picture field has the proper ID
        self.fields['profile_picture'].widget.attrs.update({'id': 'id_profile_picture'})
        
        # Hide fields based on user role
        if self.instance and self.instance.pk:
            # Hide doctor-specific fields for non-doctors
            if self.instance.role != User.DOCTOR:
                doctor_fields = ['specialization', 'doctor_license_number', 'is_available']
                for field_name in doctor_fields:
                    self.fields[field_name].widget = forms.HiddenInput()
            
            # Hide nurse-specific fields for non-nurses
            if self.instance.role != User.NURSE:
                nurse_fields = ['nurse_license_number', 'nursing_specialty']
                for field_name in nurse_fields:
                    self.fields[field_name].widget = forms.HiddenInput()
            
            # Hide pharmacist-specific fields for non-pharmacists
            if self.instance.role != User.PHARMACIST:
                pharmacist_fields = ['pharmacist_license_number', 'pharmacy_certification']
                for field_name in pharmacist_fields:
                    self.fields[field_name].widget = forms.HiddenInput()
    
    def save(self, commit=True):
        """Override save to handle profile picture properly"""
        user = super().save(commit=False)
        
        # Handle profile picture - don't clear if no new picture is provided
        if not self.cleaned_data.get('profile_picture') and not self.cleaned_data.get('profile_picture-clear') and self.instance.profile_picture:
            user.profile_picture = self.instance.profile_picture
            
        if commit:
            user.save()
            self.save_m2m()
            
        return user


class AdminUserUpdateForm(UserChangeForm):
    """Form for admin to update users"""
    
    # Custom field for nurse floor assignments
    assigned_floors = forms.MultipleChoiceField(
        choices=[
            (1, 'Floor 1 - General Medicine'),
            (2, 'Floor 2 - Cardiology'),
            (3, 'Floor 3 - Orthopedic'),
            (4, 'Floor 4 - Neurology'),
            (5, 'Floor 5 - Oncology'),
            (6, 'Floor 6 - Emergency/ICU'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        help_text="Select the floors this nurse is assigned to work on."
    )
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone_number', 
                 'address', 'profile_picture', 'qualification', 'years_of_experience',
                 # Doctor fields
                 'specialization', 'doctor_license_number', 'is_available',
                 # Nurse fields
                 'nurse_license_number', 'nursing_specialty',
                 # Pharmacist fields
                 'pharmacist_license_number', 'pharmacy_certification',
                 # Administrative fields
                 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['groups', 'user_permissions', 'is_active', 
                                  'is_staff', 'is_superuser', 'is_available', 'assigned_floors']:
                field.widget.attrs['class'] = 'form-control'
                
        # Set the choices for specialization
        self.fields['specialization'].widget = forms.Select(choices=User.SPECIALIZATION_CHOICES)
        self.fields['specialization'].widget.attrs['class'] = 'form-select'
        
        # Set checkbox widget for is_available
        self.fields['is_available'].widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})
        
        # Set checkbox widgets for boolean fields
        for field_name in ['is_active', 'is_staff', 'is_superuser']:
            self.fields[field_name].widget.attrs['class'] = 'form-check-input'
            
        # Conditionally show specialization and qualification fields based on role
        self.fields['specialization'].widget.attrs['data-role-dependent'] = 'DOCTOR'
        self.fields['doctor_license_number'].widget.attrs['data-role-dependent'] = 'DOCTOR'
        self.fields['is_available'].widget.attrs['data-role-dependent'] = 'DOCTOR'
        
        self.fields['nurse_license_number'].widget.attrs['data-role-dependent'] = 'NURSE'
        self.fields['nursing_specialty'].widget.attrs['data-role-dependent'] = 'NURSE'
        self.fields['assigned_floors'].widget.attrs['data-role-dependent'] = 'NURSE'
        
        self.fields['pharmacist_license_number'].widget.attrs['data-role-dependent'] = 'PHARMACIST'
        self.fields['pharmacy_certification'].widget.attrs['data-role-dependent'] = 'PHARMACIST'
        
        # Initialize assigned floors for existing nurses
        if self.instance and self.instance.pk and self.instance.role == User.NURSE:
            try:
                # Import here to avoid circular imports
                from patient.models import Nurse
                nurse_assignment = Nurse.objects.get(nurse=self.instance)
                if nurse_assignment.assigned_floors:
                    self.initial['assigned_floors'] = [str(floor) for floor in nurse_assignment.assigned_floors]
            except Nurse.DoesNotExist:
                pass

    def clean_assigned_floors(self):
        """Convert string floor numbers back to integers"""
        floors = self.cleaned_data.get('assigned_floors', [])
        return [int(floor) for floor in floors] if floors else []

    def save(self, commit=True):
        """Override save to handle nurse floor assignments"""
        user = super().save(commit=commit)
        
        # Handle nurse floor assignments
        if user.role == User.NURSE:
            try:
                # Import here to avoid circular imports
                from patient.models import Nurse
                
                # Get or create nurse assignment
                nurse_assignment, created = Nurse.objects.get_or_create(nurse=user)
                
                # Update assigned floors
                assigned_floors = self.cleaned_data.get('assigned_floors', [])
                nurse_assignment.assigned_floors = assigned_floors
                
                # Auto-set specialization based on primary floor if not already set
                if assigned_floors and not nurse_assignment.specialization:
                    primary_floor = assigned_floors[0]
                    specialization_map = {
                        1: 'GENERAL_MEDICINE',
                        2: 'CARDIOLOGY',
                        3: 'ORTHOPEDIC',
                        4: 'NEUROLOGY',
                        5: 'ONCOLOGY',
                        6: 'EMERGENCY',
                    }
                    nurse_assignment.specialization = specialization_map.get(primary_floor, 'GENERAL_NURSING')
                
                nurse_assignment.save()
                
            except Exception as e:
                # Log the error but don't prevent user save
                print(f"Error updating nurse floor assignments: {e}")
        
        return user


class ForgotPasswordForm(forms.Form):
    """Form for initiating password reset"""
    employee_id = forms.CharField(
        label="License Number or Employee ID",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your license number or employee ID'})
    )
    email = forms.EmailField(
        label="Registered Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your registered email'})
    )


class OTPVerificationForm(forms.Form):
    """Form for OTP verification"""
    otp = forms.CharField(
        label="OTP Code",
        max_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter 6-digit OTP',
            'autocomplete': 'off'
        })
    )


class SetNewPasswordForm(forms.Form):
    """Form for setting new password after OTP verification"""
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'})
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data 