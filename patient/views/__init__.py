"""Views package for the patient app (split by feature).

Every view is re-exported so ``from . import views`` and
``patient.views.<name>`` keep working unchanged.
"""
from .patients import (
    patient_list,
    patient_register,
    patient_detail,
    patient_update,
    patient_list_ajax,
    patient_search_api,
)
from .medical_records import (
    create_medical_record,
    view_medical_record,
    update_medical_record,
    medical_record_pdf,
    delete_medical_record,
    recent_medical_records,
)
from .rooms import (
    room_list,
    room_create,
    room_detail,
    room_update,
    bed_list,
    bed_create,
    bed_update,
    bed_search_api,
)
from .admissions import (
    admission_list,
    admission_create,
    admission_detail,
    admission_discharge,
    emergency_admission,
)
from .admission_requests import (
    admission_request_create,
    admission_request_list,
    admission_request_detail,
    admission_request_process,
    admission_request_assign_room,
)
from .nurse import (
    nurse_prescription_list,
    nurse_prescription_detail,
    nurse_medication_administration,
)
from .reports import (
    assigned_patients,
    pdf_reports,
    patient_statistics,
)

__all__ = [
    "patient_list",
    "patient_register",
    "patient_detail",
    "patient_update",
    "patient_list_ajax",
    "patient_search_api",
    "create_medical_record",
    "view_medical_record",
    "update_medical_record",
    "medical_record_pdf",
    "delete_medical_record",
    "recent_medical_records",
    "room_list",
    "room_create",
    "room_detail",
    "room_update",
    "bed_list",
    "bed_create",
    "bed_update",
    "bed_search_api",
    "admission_list",
    "admission_create",
    "admission_detail",
    "admission_discharge",
    "emergency_admission",
    "admission_request_create",
    "admission_request_list",
    "admission_request_detail",
    "admission_request_process",
    "admission_request_assign_room",
    "nurse_prescription_list",
    "nurse_prescription_detail",
    "nurse_medication_administration",
    "assigned_patients",
    "pdf_reports",
    "patient_statistics",
]
