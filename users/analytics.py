"""
Hospital-wide analytics for the admin dashboard.

Aggregates metrics across all apps. Imports app models lazily inside the
function to avoid import-time circular dependencies.
"""
from datetime import timedelta


def hospital_analytics():
    from django.db.models import Sum, F
    from django.utils import timezone

    from core.constants import FLOOR_DEPARTMENT_MAP
    from users.models import User
    from patient.models import Patient, PatientAdmission, Bed, AdmissionRequest, MedicalRecord
    from appointment.models import Appointment, DoctorLeaveRequest
    from pharmacy.models import MedicineItem, InventoryItem, Sale, DrugRequest
    from website.models import ContactInquiry, AppointmentInquiry

    today = timezone.now().date()
    month_ago = timezone.now() - timedelta(days=30)

    # --- Staff ---------------------------------------------------------
    staff_by_role = [
        {'role': label, 'count': User.objects.filter(role=value).count()}
        for value, label in User.ROLE_CHOICES
    ]
    total_staff = User.objects.count()

    # --- Patients & care ----------------------------------------------
    patients_total = Patient.objects.count()
    patients_new_30d = Patient.objects.filter(registration_date__gte=month_ago).count()
    medical_records_total = MedicalRecord.objects.count()

    # --- Appointments --------------------------------------------------
    appts = Appointment.objects
    appointments_by_status = [
        {'status': label, 'count': appts.filter(status=value).count()}
        for value, label in Appointment.STATUS_CHOICES
    ]
    appointments = {
        'total': appts.count(),
        'today': appts.filter(date=today).count(),
        'upcoming': appts.filter(date__gte=today,
                                 status__in=[Appointment.SCHEDULED, Appointment.CONFIRMED]).count(),
        'by_status': appointments_by_status,
    }

    # --- Beds & admissions --------------------------------------------
    beds_total = Bed.objects.count()
    beds_occupied = Bed.objects.filter(is_occupied=True).count()
    occupancy_rate = round(beds_occupied / beds_total * 100) if beds_total else 0
    floor_occupancy = []
    for floor in range(1, 7):
        beds_f = Bed.objects.filter(room__floor=floor)
        total = beds_f.count()
        occ = beds_f.filter(is_occupied=True).count()
        floor_occupancy.append({
            'floor': floor,
            'department': FLOOR_DEPARTMENT_MAP.get(floor, '').replace('_', ' ').title(),
            'total': total,
            'occupied': occ,
            'available': total - occ,
            'rate': round(occ / total * 100) if total else 0,
        })
    admissions = {
        'active': PatientAdmission.objects.filter(discharge_date__isnull=True).count(),
        'beds_total': beds_total,
        'beds_occupied': beds_occupied,
        'beds_available': beds_total - beds_occupied,
        'occupancy_rate': occupancy_rate,
        'requests_pending': AdmissionRequest.objects.filter(status=AdmissionRequest.PENDING).count(),
        'by_floor': floor_occupancy,
    }

    # --- Pharmacy & inventory -----------------------------------------
    pharmacy = {
        'medicines_total': MedicineItem.objects.filter(is_active=True).count(),
        'low_stock': MedicineItem.objects.filter(is_active=True,
                                                 stock_quantity__lte=F('reorder_level')).count(),
        'expired': MedicineItem.objects.filter(is_active=True, expiry_date__lte=today).count(),
        'inventory_total': InventoryItem.objects.filter(is_active=True).count(),
        'inventory_low_stock': InventoryItem.objects.filter(is_active=True,
                                                            stock_quantity__lte=F('reorder_level')).count(),
        'sales_count': Sale.objects.count(),
        'revenue_total': Sale.objects.aggregate(t=Sum('total'))['t'] or 0,
        'revenue_30d': Sale.objects.filter(sale_date__gte=month_ago).aggregate(t=Sum('total'))['t'] or 0,
        'drug_requests_pending': DrugRequest.objects.filter(status=DrugRequest.PENDING).count(),
        'drug_requests_dispensed': DrugRequest.objects.filter(status=DrugRequest.DISPENSED).count(),
    }

    # --- Front desk / website -----------------------------------------
    front_desk = {
        'contact_inquiries_pending': ContactInquiry.objects.filter(status='PENDING').count(),
        'appointment_inquiries_pending': AppointmentInquiry.objects.filter(status='PENDING').count(),
        'leave_requests_pending': DoctorLeaveRequest.objects.filter(status=DoctorLeaveRequest.PENDING).count(),
    }

    # --- Recent activity ----------------------------------------------
    recent_admissions = (PatientAdmission.objects
                         .select_related('patient', 'bed', 'bed__room')
                         .order_by('-admission_date')[:5])
    recent_sales = Sale.objects.select_related('patient').order_by('-sale_date')[:5]

    return {
        'total_staff': total_staff,
        'staff_by_role': staff_by_role,
        'patients_total': patients_total,
        'patients_new_30d': patients_new_30d,
        'medical_records_total': medical_records_total,
        'appointments': appointments,
        'admissions': admissions,
        'pharmacy': pharmacy,
        'front_desk': front_desk,
        'recent_admissions': recent_admissions,
        'recent_sales': recent_sales,
    }
