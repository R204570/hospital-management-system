"""Forms package for the patient app (split by feature).

Every view is re-exported so ``from . import views`` and
``patient.forms.<name>`` keep working unchanged.
"""
from .patients import (
    PatientRegistrationForm,
    PatientSearchForm,
)
from .medical_records import (
    MedicalRecordForm,
    MedicalRecordFilterForm,
)
from .rooms import (
    RoomForm,
    BedForm,
    NurseAssignmentForm,
)
from .admissions import (
    PatientAdmissionForm,
    EmergencyAdmissionForm,
    AdmissionRequestForm,
)

__all__ = [
    "PatientRegistrationForm",
    "PatientSearchForm",
    "MedicalRecordForm",
    "MedicalRecordFilterForm",
    "RoomForm",
    "BedForm",
    "NurseAssignmentForm",
    "PatientAdmissionForm",
    "EmergencyAdmissionForm",
    "AdmissionRequestForm",
]
