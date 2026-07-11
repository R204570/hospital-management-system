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
def supplier_list(request):
    """View for listing suppliers"""
    search_query = request.GET.get('search', '')
    
    suppliers = Supplier.objects.all()
    
    # Apply search filter
    if search_query:
        suppliers = suppliers.filter(
            Q(name__icontains=search_query) | 
            Q(contact_person__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(suppliers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'active_tab': 'suppliers'
    }
    
    return render(request, 'pharmacy/supplier_list.html', context)


@pharmacist_required
def add_supplier(request):
    """View for adding a new supplier"""
    if request.method == 'POST':
        # Process form data
        name = request.POST.get('name')
        country = request.POST.get('country')
        contact_person = request.POST.get('contact_person')
        representative = request.POST.get('representative')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        address = request.POST.get('address')
        website = request.POST.get('website')
        
        try:
            # Create supplier
            supplier = Supplier(
                name=name,
                country=country,
                contact_person=contact_person,
                representative=representative,
                phone=phone,
                email=email,
                address=address,
                website=website,
                is_active=True
            )
            supplier.save()
            
            messages.success(request, f'Supplier "{supplier.name}" added successfully.')
            return redirect('supplier_list')
        
        except Exception as e:
            messages.error(request, f'Error adding supplier: {str(e)}')
    
    context = {
        'active_tab': 'suppliers'
    }
    
    return render(request, 'pharmacy/add_supplier.html', context)


@pharmacist_required
def edit_supplier(request, pk):
    """View for editing a supplier"""
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        # Process form data
        supplier.name = request.POST.get('name')
        supplier.country = request.POST.get('country')
        supplier.contact_person = request.POST.get('contact_person')
        supplier.representative = request.POST.get('representative')
        supplier.phone = request.POST.get('phone')
        supplier.email = request.POST.get('email')
        supplier.address = request.POST.get('address')
        supplier.website = request.POST.get('website')
        supplier.is_active = request.POST.get('is_active') == 'on'
        
        try:
            supplier.save()
            messages.success(request, f'Supplier "{supplier.name}" updated successfully.')
            return redirect('supplier_list')
        
        except Exception as e:
            messages.error(request, f'Error updating supplier: {str(e)}')
    
    context = {
        'supplier': supplier,
        'active_tab': 'suppliers'
    }
    
    return render(request, 'pharmacy/edit_supplier.html', context)
