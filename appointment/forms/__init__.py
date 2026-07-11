"""Forms package for the appointment app (split by feature).

Every view is re-exported so ``from . import views`` and
``appointment.forms.<name>`` keep working unchanged.
"""
from .appointments import (
    TimeSlotForm,
    AppointmentForm,
    AppointmentStatusForm,
)
from .availability import (
    DoctorAvailabilityForm,
)
from .leave import (
    DoctorLeaveRequestForm,
    LeaveRequestReviewForm,
)

__all__ = [
    "TimeSlotForm",
    "AppointmentForm",
    "AppointmentStatusForm",
    "DoctorAvailabilityForm",
    "DoctorLeaveRequestForm",
    "LeaveRequestReviewForm",
]
