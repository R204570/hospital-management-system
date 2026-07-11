"""Read-only query helpers for the pharmacy app."""
from .models import DrugRequest


def pharmacy_queue(status=None):
    """All drug requests (optionally filtered by status) for the pharmacy queue."""
    qs = DrugRequest.objects.select_related('medicine', 'patient', 'requesting_nurse')
    if status:
        qs = qs.filter(status=status)
    return qs


def drug_requests_for_nurse(nurse, status=None):
    """A nurse's own drug requests (optionally filtered by status)."""
    qs = DrugRequest.objects.select_related('medicine', 'patient').filter(requesting_nurse=nurse)
    if status:
        qs = qs.filter(status=status)
    return qs


def pending_request_count():
    """Number of requests awaiting a pharmacy response."""
    return DrugRequest.objects.filter(status=DrugRequest.PENDING).count()
