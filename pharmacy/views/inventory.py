"""Hospital inventory (equipment / surgical / consumables) management.

Head nurses and admins can add/edit items; all nurses (and pharmacists) can
view and search. This is distinct from the medicine (drug) inventory.
"""
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render

from pharmacy.models import Category, InventoryItem, Supplier
from users.decorators import head_nurse_required

VIEW_ROLES = ('NURSE', 'PHARMACIST', 'ADMIN')


def _dec(value, default='0'):
    try:
        return Decimal(str(value) if value not in (None, '') else default)
    except (InvalidOperation, ValueError):
        return Decimal(default)


def _int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _date_or_none(value):
    return value or None


@login_required
def inventory_list(request):
    """View + search the hospital inventory (all nurses / pharmacists / admin)."""
    if request.user.role not in VIEW_ROLES:
        messages.error(request, "You don't have permission to view the hospital inventory.")
        return redirect('dashboard')

    query = request.GET.get('q', '').strip()
    items = InventoryItem.objects.select_related('category', 'supplier').filter(is_active=True)
    if query:
        items = items.filter(
            Q(name__icontains=query) | Q(item_code__icontains=query) |
            Q(category__name__icontains=query) | Q(description__icontains=query)
        )
    items = items.order_by('name')
    page = Paginator(items, 25).get_page(request.GET.get('page'))

    context = {
        'items': page,
        'query': query,
        'can_manage': request.user.can_manage_inventory,
        'total_count': InventoryItem.objects.filter(is_active=True).count(),
        'low_stock_count': InventoryItem.objects.filter(
            is_active=True, stock_quantity__lte=F('reorder_level')).count(),
    }
    return render(request, 'pharmacy/inventory_list.html', context)


def _apply_post(item, request):
    """Populate an InventoryItem from POST data. Returns an error string or None."""
    name = (request.POST.get('name') or '').strip()
    item_code = (request.POST.get('item_code') or '').strip()
    category_id = request.POST.get('category')
    if not name or not item_code or not category_id:
        return 'Name, item code, and category are required.'

    # Enforce unique item_code
    dup = InventoryItem.objects.filter(item_code=item_code).exclude(pk=item.pk)
    if dup.exists():
        return f'Item code "{item_code}" is already in use.'

    item.name = name
    item.item_code = item_code
    item.description = request.POST.get('description', '')
    item.category = get_object_or_404(Category, pk=category_id)
    supplier_id = request.POST.get('supplier')
    item.supplier = Supplier.objects.filter(pk=supplier_id).first() if supplier_id else None
    item.purchase_price = _dec(request.POST.get('purchase_price'))
    item.stock_quantity = _int(request.POST.get('stock_quantity'))
    item.reorder_level = _int(request.POST.get('reorder_level'), 5)
    item.last_maintenance = _date_or_none(request.POST.get('last_maintenance'))
    item.next_maintenance = _date_or_none(request.POST.get('next_maintenance'))
    item.warranty_expiry = _date_or_none(request.POST.get('warranty_expiry'))
    item.is_disposable = request.POST.get('is_disposable') == 'on'
    return None


@head_nurse_required
def inventory_add(request):
    """Head nurse / admin: add a new hospital inventory item."""
    if request.method == 'POST':
        item = InventoryItem()
        error = _apply_post(item, request)
        if error:
            messages.error(request, error)
        else:
            item.save()
            messages.success(request, f'Added "{item.name}" to the hospital inventory.')
            return redirect('inventory_list')
    context = {
        'item': None,
        'categories': Category.objects.all(),
        'suppliers': Supplier.objects.filter(is_active=True),
    }
    return render(request, 'pharmacy/inventory_form.html', context)


@head_nurse_required
def inventory_edit(request, pk):
    """Head nurse / admin: edit a hospital inventory item."""
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        error = _apply_post(item, request)
        if error:
            messages.error(request, error)
        else:
            item.save()
            messages.success(request, f'Updated "{item.name}".')
            return redirect('inventory_list')
    context = {
        'item': item,
        'categories': Category.objects.all(),
        'suppliers': Supplier.objects.filter(is_active=True),
    }
    return render(request, 'pharmacy/inventory_form.html', context)
