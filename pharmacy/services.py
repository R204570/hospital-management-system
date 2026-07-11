"""Business logic for the pharmacy app (drug-request workflow, dispensing)."""
from django.db import transaction
from django.utils import timezone

from .models import DrugRequest


def create_drug_request(*, nurse, patient, medicine, quantity, urgency, reason=''):
    """Create a new PENDING drug request from a nurse."""
    return DrugRequest.objects.create(
        requesting_nurse=nurse,
        patient=patient,
        medicine=medicine,
        quantity=quantity,
        urgency=urgency,
        reason=reason,
    )


def respond_to_drug_request(drug_request, pharmacist, action, approved_quantity=None, notes=''):
    """Pharmacy approves or rejects a PENDING request.

    Raises ValueError if the request is not pending or the action is invalid.
    """
    if drug_request.status != DrugRequest.PENDING:
        raise ValueError("Only pending requests can be responded to.")

    drug_request.responded_by = pharmacist
    drug_request.responded_at = timezone.now()
    drug_request.response_notes = notes or ''

    if action == 'approve':
        qty = approved_quantity or drug_request.quantity
        if qty <= 0:
            raise ValueError("Approved quantity must be greater than zero.")
        drug_request.status = DrugRequest.APPROVED
        drug_request.approved_quantity = qty
    elif action == 'reject':
        drug_request.status = DrugRequest.REJECTED
    else:
        raise ValueError("Invalid action.")

    drug_request.save()
    return drug_request


def dispense_drug_request(drug_request, pharmacist):
    """Dispense an APPROVED request: deduct stock and mark DISPENSED.

    Runs atomically. Raises ValueError on wrong status or insufficient stock.
    """
    if drug_request.status != DrugRequest.APPROVED:
        raise ValueError("Only approved requests can be dispensed.")

    qty = drug_request.approved_quantity or drug_request.quantity
    medicine = drug_request.medicine
    if medicine.stock_quantity < qty:
        raise ValueError(
            f"Insufficient stock for {medicine.name}: "
            f"{medicine.stock_quantity} available, {qty} required."
        )

    with transaction.atomic():
        medicine.stock_quantity = medicine.stock_quantity - qty
        medicine.save(update_fields=['stock_quantity', 'updated_at'])
        drug_request.status = DrugRequest.DISPENSED
        drug_request.dispensed_at = timezone.now()
        if not drug_request.approved_quantity:
            drug_request.approved_quantity = qty
        if pharmacist and not drug_request.responded_by:
            drug_request.responded_by = pharmacist
        drug_request.save()

    return drug_request


def cancel_drug_request(drug_request):
    """Nurse cancels their own PENDING request."""
    if drug_request.status != DrugRequest.PENDING:
        raise ValueError("Only pending requests can be cancelled.")
    drug_request.status = DrugRequest.CANCELLED
    drug_request.save(update_fields=['status'])
    return drug_request
