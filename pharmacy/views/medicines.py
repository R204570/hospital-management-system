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


@login_required
def medicine_list(request):  # viewable by nurses (read-only) + pharmacist/admin
    """View for listing medicines"""
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    medicines = MedicineItem.objects.all()
    
    # Apply filters
    if search_query:
        medicines = medicines.filter(
            Q(name__icontains=search_query) | 
            Q(generic_name__icontains=search_query)
        )
    
    if category_filter:
        medicines = medicines.filter(category__id=category_filter)
    
    # Get all categories for filter dropdown
    categories = Category.objects.filter(type=Category.MEDICINE)
    
    # Pagination
    paginator = Paginator(medicines, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'categories': categories,
        'active_tab': 'medicines'
    }
    
    return render(request, 'pharmacy/medicine_list.html', context)


@pharmacist_required
def medicine_detail(request, pk):
    """View for medicine details"""
    medicine = get_object_or_404(MedicineItem, pk=pk)
    
    # Get purchase history
    purchases = PurchaseItem.objects.filter(medicine=medicine).order_by('-purchase__purchase_date')
    
    # Get sales history
    sales = SaleItem.objects.filter(medicine=medicine).order_by('-sale__sale_date')
    
    context = {
        'medicine': medicine,
        'purchases': purchases,
        'sales': sales,
        'active_tab': 'medicines'
    }
    
    return render(request, 'pharmacy/medicine_detail.html', context)


@pharmacist_required
def add_medicine(request):
    """View for adding a new medicine"""
    if request.method == 'POST':
        # Process form data
        name = request.POST.get('name')
        generic_name = request.POST.get('generic_name')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        supplier_id = request.POST.get('supplier')
        purchase_price = request.POST.get('purchase_price')
        selling_price = request.POST.get('selling_price')
        stock_quantity = request.POST.get('stock_quantity', 0)
        reorder_level = request.POST.get('reorder_level', 10)
        dosage_form = request.POST.get('dosage_form')
        strength = request.POST.get('strength')
        manufacturer = request.POST.get('manufacturer')
        requires_prescription = request.POST.get('requires_prescription') == 'on'
        expiry_date = request.POST.get('expiry_date')
        batch_number = request.POST.get('batch_number')
        
        # Validate required fields
        if not name or not category_id or not purchase_price or not selling_price or not manufacturer:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('add_medicine')
        
        try:
            # Get related objects
            category = Category.objects.get(id=category_id)
            supplier = None
            if supplier_id:
                supplier = Supplier.objects.get(id=supplier_id)
            
            # Create medicine item
            medicine = MedicineItem(
                name=name,
                generic_name=generic_name,
                description=description,
                category=category,
                supplier=supplier,
                purchase_price=purchase_price,
                selling_price=selling_price,
                stock_quantity=stock_quantity,
                reorder_level=reorder_level,
                dosage_form=dosage_form,
                strength=strength,
                manufacturer=manufacturer,
                requires_prescription=requires_prescription,
                batch_number=batch_number
            )
            
            if expiry_date:
                medicine.expiry_date = expiry_date
                
            medicine.save()
            messages.success(request, f'Medicine "{medicine.name}" added successfully.')
            return redirect('medicine_detail', pk=medicine.id)
        
        except Exception as e:
            messages.error(request, f'Error adding medicine: {str(e)}')
    
    # Get all categories and suppliers for the form
    categories = Category.objects.filter(type=Category.MEDICINE)
    suppliers = Supplier.objects.filter(is_active=True)
    
    context = {
        'categories': categories,
        'suppliers': suppliers,
        'active_tab': 'medicines'
    }
    
    return render(request, 'pharmacy/add_medicine.html', context)


@pharmacist_required
def edit_medicine(request, pk):
    """View for editing a medicine"""
    medicine = get_object_or_404(MedicineItem, pk=pk)
    
    if request.method == 'POST':
        # Process form data
        medicine.name = request.POST.get('name')
        medicine.generic_name = request.POST.get('generic_name')
        medicine.description = request.POST.get('description')
        
        category_id = request.POST.get('category')
        supplier_id = request.POST.get('supplier')
        
        medicine.purchase_price = request.POST.get('purchase_price')
        medicine.selling_price = request.POST.get('selling_price')
        medicine.stock_quantity = request.POST.get('stock_quantity', 0)
        medicine.reorder_level = request.POST.get('reorder_level', 10)
        medicine.dosage_form = request.POST.get('dosage_form')
        medicine.strength = request.POST.get('strength')
        medicine.manufacturer = request.POST.get('manufacturer')
        medicine.requires_prescription = request.POST.get('requires_prescription') == 'on'
        medicine.batch_number = request.POST.get('batch_number')
        
        expiry_date = request.POST.get('expiry_date')
        if expiry_date:
            medicine.expiry_date = expiry_date
        
        # Validate required fields
        if not medicine.name or not category_id or not medicine.purchase_price or not medicine.selling_price or not medicine.manufacturer:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('edit_medicine', pk=medicine.id)
            
        try:
            # Get related objects
            medicine.category = Category.objects.get(id=category_id)
            
            if supplier_id:
                medicine.supplier = Supplier.objects.get(id=supplier_id)
            else:
                medicine.supplier = None
            
            medicine.save()
            messages.success(request, f'Medicine "{medicine.name}" updated successfully.')
            return redirect('medicine_detail', pk=medicine.id)
        
        except Exception as e:
            messages.error(request, f'Error updating medicine: {str(e)}')
    
    # Get all categories and suppliers for the form
    categories = Category.objects.filter(type=Category.MEDICINE)
    suppliers = Supplier.objects.filter(is_active=True)
    
    context = {
        'medicine': medicine,
        'categories': categories,
        'suppliers': suppliers,
        'active_tab': 'medicines'
    }
    
    return render(request, 'pharmacy/edit_medicine.html', context)


def medicine_search_api(request):
    """API endpoint for medicine search with autocomplete suggestions"""
    query = request.GET.get('query', '')
    results = []
    
    if query and len(query) >= 2:  # Only search if query is at least 2 characters
        medicines = MedicineItem.objects.filter(
            Q(name__icontains=query) | 
            Q(generic_name__icontains=query)
        ).order_by('name')[:10]  # Limit to 10 results
        
        # Format results
        for medicine in medicines:
            results.append({
                'id': medicine.id,
                'name': medicine.name,
                'generic_name': medicine.generic_name or '',
                'strength': medicine.strength or '',
                'manufacturer': medicine.manufacturer or '',
                'category': medicine.category.name
            })
    
    return JsonResponse({'results': results})


@pharmacist_required
def low_stock_list(request):
    """View for listing low stock items"""
    low_stock_items = MedicineItem.objects.filter(
        is_active=True, 
        stock_quantity__lte=F('reorder_level')
    ).order_by('stock_quantity')
    
    # Pagination
    paginator = Paginator(low_stock_items, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'active_tab': 'low_stock'
    }
    
    return render(request, 'pharmacy/low_stock_list.html', context)


@pharmacist_required
def expired_medicines(request):
    """View for listing expired medicines"""
    today = timezone.now().date()
    
    expired_items = MedicineItem.objects.filter(
        is_active=True,
        expiry_date__isnull=False,
        expiry_date__lt=today
    ).order_by('expiry_date')
    
    # Pagination
    paginator = Paginator(expired_items, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'active_tab': 'expired'
    }
    
    return render(request, 'pharmacy/expired_medicines.html', context)
