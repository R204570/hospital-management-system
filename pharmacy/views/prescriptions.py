from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F, Count
from pharmacy.models import (
    Category, Supplier, MedicineItem, InventoryItem, 
    Purchase, PurchaseItem, Sale, SaleItem
)
from patient.models import MedicalRecord
from users.models import User
from users.decorators import pharmacist_required
import datetime
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse


@pharmacist_required
def prescription_list(request):
    """View for displaying prescriptions to be filled by pharmacy"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # Get medical records with prescriptions
    medical_records = MedicalRecord.objects.filter(
        prescription__isnull=False
    ).exclude(prescription__exact='')
    
    # Apply filters
    if search_query:
        medical_records = medical_records.filter(
            Q(patient__first_name__icontains=search_query) | 
            Q(patient__last_name__icontains=search_query) |
            Q(doctor__first_name__icontains=search_query) |
            Q(doctor__last_name__icontains=search_query) |
            Q(diagnosis__icontains=search_query)
        )
    
    # Get current date
    today = timezone.now().date()
    
    # Sort by date (newest first)
    medical_records = medical_records.order_by('-report_date')
    
    # Pagination
    paginator = Paginator(medical_records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'today': today,
    }
    
    return render(request, 'pharmacy/prescription_list.html', context)
