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



def extract_common_keywords(diagnoses, limit=10):
    """Helper function to extract common keywords from diagnoses"""
    # This is a simple implementation - in a real system, you'd use NLP techniques
    all_words = []
    for diagnosis in diagnoses:
        # Split by spaces and punctuation
        words = re.findall(r'\b\w+\b', diagnosis.lower())
        all_words.extend(words)
    
    # Remove common English stopwords
    stopwords = {'the', 'and', 'or', 'a', 'an', 'of', 'to', 'with', 'in', 'on', 'for'}
    filtered_words = [word for word in all_words if word not in stopwords and len(word) > 2]
    
    # Count occurrences and return most common
    word_counts = Counter(filtered_words)
    return word_counts.most_common(limit)
