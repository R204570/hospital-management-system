from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
import datetime
import json
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import logging
from django.core.paginator import Paginator
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from appointment.models import Appointment, DoctorAvailability, DoctorLeaveRequest
from appointment.forms import AppointmentForm, TimeSlotForm, DoctorAvailabilityForm, AppointmentStatusForm, DoctorLeaveRequestForm, LeaveRequestReviewForm
from patient.models import Patient
from users.models import User
from users.decorators import doctor_required, receptionist_required, nurse_required, pharmacist_required, admin_required, role_required
from website.models import AppointmentInquiry, ContactInquiry


@doctor_required
def manage_availability(request):
    if request.method == 'POST':
        form = DoctorAvailabilityForm(request.POST)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.doctor = request.user
            try:
                availability.save()
                messages.success(request, 'Availability added successfully.')
                return redirect('manage_availability')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = DoctorAvailabilityForm()
    
    # Get all availability slots for the doctor
    availabilities = DoctorAvailability.objects.filter(doctor=request.user)
    
    context = {
        'form': form,
        'availabilities': availabilities
    }
    
    return render(request, 'appointment/manage_availability.html', context)


@doctor_required
def delete_availability(request, pk):
    try:
        availability = DoctorAvailability.objects.get(pk=pk, doctor=request.user)
        availability.delete()
        messages.success(request, 'Availability slot deleted successfully.')
    except DoctorAvailability.DoesNotExist:
        messages.error(request, 'Availability slot not found.')
    
    return redirect('manage_availability')
