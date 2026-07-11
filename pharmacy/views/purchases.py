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
def purchase_list(request):
    """View for listing purchase orders"""
    status_filter = request.GET.get('status', '')
    
    purchases = Purchase.objects.all()
    
    # Apply status filter
    if status_filter:
        purchases = purchases.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(purchases, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'active_tab': 'purchases'
    }
    
    return render(request, 'pharmacy/purchase_list.html', context)


@pharmacist_required
def add_purchase(request):
    """View for creating a new purchase order"""
    if request.method == 'POST':
        # Process main purchase data
        supplier_id = request.POST.get('supplier')
        purchase_date = request.POST.get('purchase_date')
        notes = request.POST.get('notes')
        
        try:
            supplier = Supplier.objects.get(id=supplier_id)
            
            # Create purchase
            purchase = Purchase(
                supplier=supplier,
                purchase_date=purchase_date,
                status=Purchase.PENDING,
                payment_status='Unpaid',
                notes=notes,
                created_by=request.user
            )
            purchase.save()
            
            # Process purchase items
            medicine_ids = request.POST.getlist('medicine_id')
            quantities = request.POST.getlist('quantity')
            unit_prices = request.POST.getlist('unit_price')
            expiry_dates = request.POST.getlist('expiry_date')
            batch_numbers = request.POST.getlist('batch_number')
            
            for i in range(len(medicine_ids)):
                if medicine_ids[i] and quantities[i] and unit_prices[i]:
                    medicine = MedicineItem.objects.get(id=medicine_ids[i])
                    
                    item = PurchaseItem(
                        purchase=purchase,
                        medicine=medicine,
                        quantity=quantities[i],
                        unit_price=unit_prices[i],
                        batch_number=batch_numbers[i] if batch_numbers[i] else None
                    )
                    
                    if expiry_dates[i]:
                        item.expiry_date = expiry_dates[i]
                    
                    item.save()
            
            messages.success(request, f'Purchase order created successfully.')
            return redirect('purchase_detail', pk=purchase.id)
        
        except Exception as e:
            messages.error(request, f'Error creating purchase order: {str(e)}')
    
    # Get suppliers and medicines for the form
    suppliers = Supplier.objects.filter(is_active=True)
    medicines = MedicineItem.objects.filter(is_active=True)
    
    context = {
        'suppliers': suppliers,
        'medicines': medicines,
        'active_tab': 'purchases'
    }
    
    return render(request, 'pharmacy/add_purchase.html', context)


@pharmacist_required
def purchase_detail(request, pk):
    """View for purchase order details"""
    purchase = get_object_or_404(Purchase, pk=pk)
    items = purchase.items.all()
    
    context = {
        'purchase': purchase,
        'items': items,
        'active_tab': 'purchases'
    }
    
    return render(request, 'pharmacy/purchase_detail.html', context)


@pharmacist_required
def receive_purchase(request, pk):
    """View for receiving purchase orders"""
    purchase = get_object_or_404(Purchase, pk=pk)
    
    if request.method == 'POST':
        if purchase.status != Purchase.PENDING:
            messages.error(request, 'This purchase order has already been processed.')
            return redirect('purchase_detail', pk=purchase.id)
        
        try:
            # Update purchase status
            purchase.status = Purchase.RECEIVED
            purchase.save()
            
            # Process received items
            for item in purchase.items.all():
                received_qty = int(request.POST.get(f'received_qty_{item.id}', 0))
                item.received_quantity = received_qty
                item.save()
                
                # Update medicine stock and details
                if item.medicine:
                    medicine = item.medicine
                    medicine.stock_quantity += received_qty
                    
                    # Update expiry date and batch number if provided
                    if item.expiry_date:
                        medicine.expiry_date = item.expiry_date
                    if item.batch_number:
                        medicine.batch_number = item.batch_number
                    
                    medicine.save()
            
            messages.success(request, 'Purchase order received successfully.')
            return redirect('purchase_detail', pk=purchase.id)
        
        except Exception as e:
            messages.error(request, f'Error receiving purchase order: {str(e)}')
    
    context = {
        'purchase': purchase,
        'items': purchase.items.all(),
        'active_tab': 'purchases'
    }
    
    return render(request, 'pharmacy/receive_purchase.html', context)


@pharmacist_required
def cancel_purchase(request, pk):
    """View for cancelling purchase orders"""
    purchase = get_object_or_404(Purchase, pk=pk)
    
    if request.method == 'POST':
        if purchase.status == Purchase.RECEIVED:
            messages.error(request, 'Cannot cancel a received purchase order.')
            return redirect('purchase_detail', pk=purchase.id)
        
        purchase.status = Purchase.CANCELLED
        purchase.save()
        
        messages.success(request, 'Purchase order cancelled successfully.')
        return redirect('purchase_detail', pk=purchase.id)
    
    context = {
        'purchase': purchase,
        'active_tab': 'purchases'
    }
    
    return render(request, 'pharmacy/cancel_purchase.html', context)
