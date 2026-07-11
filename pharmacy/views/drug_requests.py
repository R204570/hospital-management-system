"""Nurse <-> Pharmacy drug-request workflow views."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from patient.models import Patient
from pharmacy import selectors, services
from pharmacy.models import DrugRequest, MedicineItem
from users.decorators import nurse_required, pharmacist_required


# --------------------------------------------------------------------------
# Nurse side
# --------------------------------------------------------------------------
@nurse_required
def drug_request_create(request, patient_id=None):
    """Nurse submits a new drug request to the pharmacy."""
    selected_patient = get_object_or_404(Patient, pk=patient_id) if patient_id else None

    if request.method == 'POST':
        try:
            patient = get_object_or_404(Patient, pk=request.POST.get('patient'))
            medicine = get_object_or_404(MedicineItem, pk=request.POST.get('medicine'))
            quantity = int(request.POST.get('quantity') or 0)
            urgency = request.POST.get('urgency') or DrugRequest.ROUTINE
            reason = request.POST.get('reason', '').strip()

            if quantity <= 0:
                messages.error(request, 'Quantity must be greater than zero.')
            else:
                dr = services.create_drug_request(
                    nurse=request.user, patient=patient, medicine=medicine,
                    quantity=quantity, urgency=urgency, reason=reason,
                )
                messages.success(
                    request, f'Drug request DR-{dr.pk} submitted for {medicine.name} (x{quantity}).'
                )
                return redirect('nurse_drug_request_list')
        except (ValueError, TypeError):
            messages.error(request, 'Please select a valid patient, medicine, and quantity.')

    context = {
        'patients': Patient.objects.order_by('first_name', 'last_name'),
        'medicines': MedicineItem.objects.filter(is_active=True).order_by('name'),
        'selected_patient': selected_patient,
        'urgency_choices': DrugRequest.URGENCY_CHOICES,
    }
    return render(request, 'pharmacy/drug_request_form.html', context)


@nurse_required
def nurse_drug_request_list(request):
    """List the requests submitted by the current nurse."""
    status = request.GET.get('status', '')
    drug_requests = selectors.drug_requests_for_nurse(request.user, status or None)
    context = {
        'drug_requests': drug_requests,
        'status_filter': status,
        'status_choices': DrugRequest.STATUS_CHOICES,
        'pending_count': selectors.drug_requests_for_nurse(request.user, DrugRequest.PENDING).count(),
    }
    return render(request, 'pharmacy/nurse_drug_request_list.html', context)


@nurse_required
def drug_request_cancel(request, pk):
    """Nurse cancels their own still-pending request."""
    dr = get_object_or_404(DrugRequest, pk=pk, requesting_nurse=request.user)
    if request.method == 'POST':
        try:
            services.cancel_drug_request(dr)
            messages.success(request, f'Request DR-{dr.pk} cancelled.')
        except ValueError as e:
            messages.error(request, str(e))
        return redirect('nurse_drug_request_list')
    return redirect('drug_request_detail', pk=pk)


# --------------------------------------------------------------------------
# Pharmacy side
# --------------------------------------------------------------------------
@pharmacist_required
def drug_request_queue(request):
    """Pharmacy queue of drug requests (defaults to pending)."""
    status = request.GET.get('status', DrugRequest.PENDING)
    drug_requests = selectors.pharmacy_queue(None if status == 'ALL' else status)
    context = {
        'drug_requests': drug_requests,
        'status_filter': status,
        'status_choices': DrugRequest.STATUS_CHOICES,
        'pending_count': selectors.pending_request_count(),
    }
    return render(request, 'pharmacy/drug_request_queue.html', context)


@pharmacist_required
def drug_request_respond(request, pk):
    """Pharmacy approves or rejects a pending request."""
    dr = get_object_or_404(DrugRequest, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('response_notes', '').strip()
        raw_qty = request.POST.get('approved_quantity')
        try:
            approved_quantity = int(raw_qty) if raw_qty else None
        except ValueError:
            approved_quantity = None
        try:
            services.respond_to_drug_request(
                dr, request.user, action, approved_quantity=approved_quantity, notes=notes
            )
            messages.success(request, f'Request DR-{dr.pk} {dr.get_status_display().lower()}.')
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('drug_request_detail', pk=pk)


@pharmacist_required
def drug_request_dispense(request, pk):
    """Pharmacy dispenses an approved request (deducts stock)."""
    dr = get_object_or_404(DrugRequest, pk=pk)
    if request.method == 'POST':
        try:
            services.dispense_drug_request(dr, request.user)
            messages.success(
                request, f'Dispensed {dr.approved_quantity} x {dr.medicine.name}. Inventory updated.'
            )
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('drug_request_detail', pk=pk)


# --------------------------------------------------------------------------
# Shared
# --------------------------------------------------------------------------
@login_required
def drug_request_detail(request, pk):
    """Detail view accessible to the owning nurse, any pharmacist, or admin."""
    dr = get_object_or_404(
        DrugRequest.objects.select_related(
            'medicine', 'patient', 'requesting_nurse', 'responded_by'
        ),
        pk=pk,
    )
    u = request.user
    allowed = (
        u.role in ('PHARMACIST', 'ADMIN')
        or (u.role == 'NURSE' and dr.requesting_nurse_id == u.id)
    )
    if not allowed:
        messages.error(request, "You don't have permission to view this request.")
        return redirect('dashboard')
    return render(request, 'pharmacy/drug_request_detail.html', {'dr': dr})


@login_required
def drug_request_notifications(request):
    """Polling endpoint: pending queue for pharmacy, status updates for nurses."""
    u = request.user
    if u.role in ('PHARMACIST', 'ADMIN'):
        pending = selectors.pharmacy_queue(DrugRequest.PENDING)[:10]
        return JsonResponse({
            'role': 'pharmacy',
            'pending_count': selectors.pending_request_count(),
            'items': [{
                'id': r.pk,
                'medicine': r.medicine.name,
                'quantity': r.quantity,
                'urgency': r.get_urgency_display(),
                'nurse': r.requesting_nurse.get_full_name() or r.requesting_nurse.username,
                'patient': r.patient.full_name,
                'created': r.created_at.strftime('%Y-%m-%d %H:%M'),
            } for r in pending],
        })

    if u.role == 'NURSE':
        recent = selectors.drug_requests_for_nurse(u).exclude(status=DrugRequest.PENDING)[:10]
        return JsonResponse({
            'role': 'nurse',
            'pending_count': selectors.drug_requests_for_nurse(u, DrugRequest.PENDING).count(),
            'items': [{
                'id': r.pk,
                'medicine': r.medicine.name,
                'status': r.get_status_display(),
                'status_class': r.status_badge_class,
            } for r in recent],
        })
    return JsonResponse({'role': 'other', 'pending_count': 0, 'items': []})
