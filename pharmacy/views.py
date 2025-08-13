from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F, Count
from .models import (
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


@pharmacist_required
def medicine_list(request):
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
        discount = request.POST.get('discount', 0)
        tax = request.POST.get('tax', 0)
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
                        quantity=quantities[i],
                        unit_price=unit_prices[i],
                        discount=item_discounts[i] if item_discounts[i] else 0
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
    medical_records = medical_records.order_by('-created_at')
    
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