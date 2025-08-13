from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.conf import settings
import os


class User(AbstractUser):
    """Custom User model extending Django's AbstractUser for role-based access"""
    
    # Roles for HMS staff
    ADMIN = 'ADMIN'
    DOCTOR = 'DOCTOR'
    NURSE = 'NURSE'
    RECEPTIONIST = 'RECEPTIONIST'
    PHARMACIST = 'PHARMACIST'
    
    ROLE_CHOICES = [
        (ADMIN, 'Administrator'),
        (DOCTOR, 'Doctor'),
        (NURSE, 'Nurse'),
        (RECEPTIONIST, 'Receptionist'),
        (PHARMACIST, 'Pharmacist'),
    ]
    
    # Doctor specialization choices for Multi-Specialty Hospital
    GENERAL_MEDICINE = 'GENERAL_MEDICINE'
    CARDIOLOGY = 'CARDIOLOGY'
    ORTHOPEDIC = 'ORTHOPEDIC'
    NEUROLOGY = 'NEUROLOGY'
    EMERGENCY = 'EMERGENCY'
    ONCOLOGY = 'ONCOLOGY'
    
    SPECIALIZATION_CHOICES = [
        (GENERAL_MEDICINE, 'General Medicine & Internal Medicine'),
        (CARDIOLOGY, 'Cardiology & Cardiovascular Surgery'),
        (ORTHOPEDIC, 'Orthopedic & Bone Surgery'),
        (NEUROLOGY, 'Neurology & Neurosurgery'),
        (EMERGENCY, 'Emergency Medicine & Critical Care'),
        (ONCOLOGY, 'Oncology & Cancer Treatment'),
    ]
    
    # Map specialization to floor numbers in Multi-Specialty Hospital
    SPECIALIZATION_FLOORS = {
        GENERAL_MEDICINE: 1,        # Floor 1: General Medicine & Internal Medicine
        CARDIOLOGY: 2,              # Floor 2: Cardiology & Cardiovascular Surgery
        ORTHOPEDIC: 3,              # Floor 3: Orthopedic & Bone Surgery
        NEUROLOGY: 4,               # Floor 4: Neurology & Neurosurgery
        EMERGENCY: 5,               # Floor 5: Emergency & Critical Care
        ONCOLOGY: 6,                # Floor 6: Oncology & Cancer Treatment
    }
    
    role = models.CharField(
        max_length=15,
        choices=ROLE_CHOICES,
        default=RECEPTIONIST,
    )
    
    # Additional fields for staff
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    
    # Common fields for all medical professionals
    qualification = models.CharField(max_length=255, blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    
    # Fields for doctor profile
    specialization = models.CharField(max_length=20, choices=SPECIALIZATION_CHOICES, blank=True)
    doctor_license_number = models.CharField(max_length=50, blank=True, help_text="Doctor's medical license number")
    is_available = models.BooleanField(default=True, help_text="Availability for appointments")
    
    # Fields for nurse profile
    nurse_license_number = models.CharField(max_length=50, blank=True, help_text="Nurse's license number")
    nursing_specialty = models.CharField(max_length=100, blank=True, help_text="Nursing specialty (e.g., ICU, ER)")
    
    # Fields for pharmacist profile
    pharmacist_license_number = models.CharField(max_length=50, blank=True, help_text="Pharmacist's license number")
    pharmacy_certification = models.CharField(max_length=100, blank=True, help_text="Pharmacy certification (e.g., PharmD)")
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def get_profile_picture_url(self):
        """Return the URL of the user's profile picture or a default image"""
        if self.profile_picture and hasattr(self.profile_picture, 'url'):
            return f"{self.profile_picture.url}?v={hash(self.pk)}"
        return None
    
    def save(self, *args, **kwargs):
        """Override save to handle profile picture changes"""
        # If this is an existing user with a new profile picture
        if self.pk:
            try:
                old_instance = User.objects.get(pk=self.pk)
                if old_instance.profile_picture and self.profile_picture and self.profile_picture != old_instance.profile_picture:
                    # Delete old picture file if it exists and is different
                    if os.path.isfile(old_instance.profile_picture.path):
                        os.remove(old_instance.profile_picture.path)
            except (User.DoesNotExist, ValueError, FileNotFoundError) as e:
                # Just log the error but continue
                print(f"Error handling old profile picture: {str(e)}")
        super().save(*args, **kwargs)
    
    @property
    def is_admin(self):
        return self.role == self.ADMIN
    
    @property
    def is_doctor(self):
        return self.role == self.DOCTOR
    
    @property
    def is_nurse(self):
        return self.role == self.NURSE
    
    @property
    def is_receptionist(self):
        return self.role == self.RECEPTIONIST
    
    @property
    def is_pharmacist(self):
        return self.role == self.PHARMACIST
    
    @property
    def get_floor(self):
        """Get assigned floor based on specialization"""
        if self.is_doctor and self.specialization:
            floors = self.SPECIALIZATION_FLOORS.get(self.specialization)
            if isinstance(floors, list):
                # If multiple floors (like oncology), return the first one as default
                return floors[0]
            return floors
        return None
    
    @property
    def license_number(self):
        """Return the appropriate license number based on role"""
        if self.is_doctor:
            return self.doctor_license_number
        elif self.is_nurse:
            return self.nurse_license_number
        elif self.is_pharmacist:
            return self.pharmacist_license_number
        return None 