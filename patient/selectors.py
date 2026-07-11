from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.http import HttpResponse, Http404, JsonResponse
from django.utils import timezone
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.core.paginator import Paginator
import re
from collections import Counter
from datetime import datetime, timedelta
from django import forms
import os
import uuid
import base64
import binascii
from django.conf import settings

from patient.models import Patient, MedicalRecord, Room, Bed, Nurse, PatientAdmission, AdmissionRequest
from patient.forms import (
    PatientRegistrationForm, PatientSearchForm, MedicalRecordForm, 
    MedicalRecordFilterForm, RoomForm, BedForm, NurseAssignmentForm,
    PatientAdmissionForm, EmergencyAdmissionForm, AdmissionRequestForm
)
from users.decorators import receptionist_required, doctor_required, admin_required, nurse_required
from users.models import User
from appointment.models import Appointment



def find_available_nurse(floor):
    """Find an available nurse for the given floor"""
    # Get nurses assigned to this floor who are on duty
    available_nurses = Nurse.objects.filter(
        floor=floor,
        is_on_duty=True
    )
    
    # Find nurses with less than max patients
    for nurse in available_nurses:
        if nurse.is_available:
            return nurse
    
    # If no nurses found with capacity, return the one with fewest patients
    if available_nurses:
        return min(
            available_nurses, 
            key=lambda n: PatientAdmission.objects.filter(
                assigned_nurse=n.nurse, 
                discharge_date__isnull=True
            ).count()
        )
    
    return None


def find_available_doctor(specialty=None):
    """Find an available doctor matching the specialty"""
    doctors_query = User.objects.filter(
        role=User.DOCTOR,
        is_available=True
    )
    
    if specialty:
        # First try to find a doctor with matching specialty
        specialty_doctors = doctors_query.filter(department=specialty)
        if specialty_doctors.exists():
            return specialty_doctors.first()
    
    # If no specialty match or no specialty provided, get any available doctor
    if doctors_query.exists():
        return doctors_query.first()
    
    return None
