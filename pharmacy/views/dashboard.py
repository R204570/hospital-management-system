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
def pharmacy_dashboard(request):
    """Dashboard view for pharmacists"""
    today = timezone.now().date()
    
    # Get current month's first and last day
    today = timezone.now().date()
    first_day = today.replace(day=1)
    if today.month == 12:
        last_day = today.replace(year=today.year + 1, month=1, day=1) - datetime.timedelta(days=1)
    else:
        last_day = today.replace(month=today.month + 1, day=1) - datetime.timedelta(days=1)
    
    # Calculate statistics
    medicines_count = MedicineItem.objects.filter(is_active=True).count()
    low_stock_count = MedicineItem.objects.filter(
        is_active=True, 
        stock_quantity__lte=F('reorder_level')
    ).count()
    
    pending_orders_count = Purchase.objects.filter(status='PENDING').count()
    
    # Get low stock items for display
    low_stock_items = MedicineItem.objects.filter(
        is_active=True, 
        stock_quantity__lte=F('reorder_level')
    ).order_by('stock_quantity')[:10]
    
    context = {
        'medicines_count': medicines_count,
        'pending_orders_count': pending_orders_count,
        'low_stock_count': low_stock_count,
        'low_stock_items': low_stock_items
    }
    
    return render(request, 'pharmacy/dashboard.html', context)
