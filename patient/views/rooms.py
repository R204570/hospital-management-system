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


@admin_required
def room_list(request):
    """View for listing all rooms"""
    rooms = Room.objects.all().order_by('floor', 'room_number')
    
    # Add bed count and occupancy to rooms
    for room in rooms:
        room.bed_count = room.beds.count()
        room.occupied_beds = room.beds.filter(is_occupied=True).count()
    
    context = {
        'rooms': rooms,
    }
    
    return render(request, 'patient/room_list.html', context)


@admin_required
def room_create(request):
    """View for creating a new room"""
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save()
            
            # Create default beds (10 per room)
            for i in range(1, 11):
                Bed.objects.create(
                    room=room,
                    bed_number=f"B{i:02d}"
                )
            
            messages.success(request, f'Room {room.room_number} created successfully with 10 beds.')
            return redirect('room_detail', pk=room.id)
    else:
        form = RoomForm()
    
    context = {
        'form': form,
        'title': 'Create New Room'
    }
    
    return render(request, 'patient/room_form.html', context)


@admin_required
def room_detail(request, pk):
    """View for room details"""
    room = get_object_or_404(Room, pk=pk)
    beds = room.beds.all()
    
    # Get current admissions for occupied beds
    for bed in beds:
        if bed.is_occupied:
            bed.current_admission = PatientAdmission.objects.filter(
                bed=bed, 
                discharge_date__isnull=True
            ).first()
    
    context = {
        'room': room,
        'beds': beds
    }
    
    return render(request, 'patient/room_detail.html', context)


@admin_required
def room_update(request, pk):
    """View for updating room details"""
    room = get_object_or_404(Room, pk=pk)
    
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, f'Room {room.room_number} updated successfully.')
            return redirect('room_detail', pk=room.id)
    else:
        form = RoomForm(instance=room)
    
    context = {
        'form': form,
        'title': f'Update Room {room.room_number}',
        'room': room
    }
    
    return render(request, 'patient/room_form.html', context)


@login_required
def bed_list(request):
    """View for listing all beds with their status"""
    beds = Bed.objects.all().select_related('room')
    
    # Filter options
    floor = request.GET.get('floor')
    status = request.GET.get('status')
    department = request.GET.get('department')
    
    if floor:
        beds = beds.filter(room__floor=floor)
    
    if status == 'available':
        beds = beds.filter(is_occupied=False)
    elif status == 'occupied':
        beds = beds.filter(is_occupied=True)
    
    if department:
        beds = beds.filter(room__department=department)
    
    # Add current patient info to occupied beds
    for bed in beds:
        if bed.is_occupied:
            bed.current_admission = PatientAdmission.objects.filter(
                bed=bed,
                discharge_date__isnull=True
            ).first()
    
    context = {
        'beds': beds,
        'floor_filter': floor,
        'status_filter': status,
        'department_filter': department,
        'department_choices': Room.DEPARTMENT_CHOICES,
    }
    
    return render(request, 'patient/bed_list.html', context)


@admin_required
def bed_create(request, room_id=None):
    """View for creating a new bed"""
    room = None
    if room_id:
        room = get_object_or_404(Room, pk=room_id)
    
    if request.method == 'POST':
        form = BedForm(request.POST)
        if form.is_valid():
            bed = form.save()
            messages.success(request, f'Bed {bed.bed_number} in Room {bed.room.room_number} created successfully.')
            
            if room:
                return redirect('room_detail', pk=room.id)
            return redirect('bed_list')
    else:
        initial = {}
        if room:
            initial['room'] = room
        form = BedForm(initial=initial)
    
    context = {
        'form': form,
        'title': 'Create New Bed',
        'room': room
    }
    
    return render(request, 'patient/bed_form.html', context)


@admin_required
def bed_update(request, pk):
    """View for updating bed details"""
    bed = get_object_or_404(Bed, pk=pk)
    
    if request.method == 'POST':
        form = BedForm(request.POST, instance=bed)
        if form.is_valid():
            form.save()
            messages.success(request, f'Bed {bed.bed_number} updated successfully.')
            return redirect('room_detail', pk=bed.room.id)
    else:
        form = BedForm(instance=bed)
    
    context = {
        'form': form,
        'title': f'Update Bed {bed.bed_number}',
        'bed': bed
    }
    
    return render(request, 'patient/bed_form.html', context)


@login_required
def bed_search_api(request):
    """AJAX endpoint for bed search"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 1:
        return JsonResponse({'results': []})
    
    # Search available beds by bed number, room number, floor, or department
    beds = Bed.objects.filter(
        is_occupied=False
    ).select_related('room').filter(
        Q(bed_number__icontains=query) |
        Q(room__room_number__icontains=query) |
        Q(room__floor__icontains=query) |
        Q(room__department__icontains=query)
    ).order_by('room__floor', 'room__room_number', 'bed_number')[:20]  # Limit to 20 results
    
    results = []
    for bed in beds:
        results.append({
            'id': bed.id,
            'text': f"Bed {bed.bed_number} - Room {bed.room.room_number} (Floor {bed.room.floor}, {bed.room.get_department_display()})",
            'bed_number': bed.bed_number,
            'room_number': bed.room.room_number,
            'floor': bed.room.floor,
            'department': bed.room.get_department_display()
        })
    
    return JsonResponse({'results': results})
