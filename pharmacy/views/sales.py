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
from decimal import Decimal
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse


@pharmacist_required
def sale_list(request):
    """View for listing sales"""
    sales = Sale.objects.all().order_by('-sale_date')
    
    # Pagination
    paginator = Paginator(sales, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'active_tab': 'sales'
    }
    
    return render(request, 'pharmacy/sale_list.html', context)


@pharmacist_required
def add_sale(request):
    """View for creating a new sale"""
    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        payment_method = request.POST.get('payment_method')
        discount = Decimal(request.POST.get('discount') or 0)
        tax = Decimal(request.POST.get('tax') or 0)
        notes = request.POST.get('notes')
        
        try:
            # Create sale
            sale = Sale(
                patient_id=patient_id if patient_id else None,
                payment_method=payment_method,
                discount=discount,
                tax=tax,
                notes=notes,
                cashier=request.user
            )
            sale.save()
            
            # Process sale items
            medicine_ids = request.POST.getlist('medicine_id[]')
            quantities = request.POST.getlist('quantity[]')
            unit_prices = request.POST.getlist('unit_price[]')
            item_discounts = request.POST.getlist('item_discount[]')
            
            for i in range(len(medicine_ids)):
                if medicine_ids[i] and quantities[i] and unit_prices[i]:
                    medicine = MedicineItem.objects.get(id=medicine_ids[i])
                    
                    item = SaleItem(
                        sale=sale,
                        medicine=medicine,
                        quantity=int(quantities[i]),
                        unit_price=Decimal(unit_prices[i]),
                        discount=Decimal(item_discounts[i]) if item_discounts[i] else 0
                    )
                    item.save()
            
            # Save again to calculate totals
            sale.save()
            
            messages.success(request, 'Sale created successfully.')
            return redirect('sale_detail', pk=sale.id)
        
        except Exception as e:
            messages.error(request, f'Error creating sale: {str(e)}')
    
    # Get patients and medicines for the form
    from patient.models import Patient
    
    patients = Patient.objects.all()
    medicines = MedicineItem.objects.filter(is_active=True, stock_quantity__gt=0)
    
    # Convert medicines to JSON for JavaScript use
    medicines_list = []
    for medicine in medicines:
        medicines_list.append({
            'id': medicine.id,
            'name': medicine.name,
            'generic_name': medicine.generic_name,
            'selling_price': float(medicine.selling_price),
            'stock_quantity': medicine.stock_quantity,
            'reorder_level': medicine.reorder_level,
            'dosage_form': medicine.dosage_form,
            'strength': medicine.strength,
            'manufacturer': medicine.manufacturer,
            'requires_prescription': medicine.requires_prescription,
        })
    
    medicines_json = json.dumps(medicines_list, cls=DjangoJSONEncoder)
    
    context = {
        'patients': patients,
        'medicines_json': medicines_json,
        'payment_methods': Sale.PAYMENT_CHOICES,
        'active_tab': 'sales'
    }
    
    return render(request, 'pharmacy/amazon_style_sale.html', context)


@pharmacist_required
def sale_detail(request, pk):
    """View for sale details"""
    sale = get_object_or_404(Sale, pk=pk)
    items = sale.items.all()
    
    context = {
        'sale': sale,
        'items': items,
        'active_tab': 'sales'
    }
    
    return render(request, 'pharmacy/sale_detail.html', context)
