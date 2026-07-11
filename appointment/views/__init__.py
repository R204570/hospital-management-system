"""Views package for the appointment app (split by feature).

Every view is re-exported so ``from . import views`` and
``appointment.views.<name>`` keep working unchanged.
"""
from .appointments import (
    appointment_list,
    book_appointment,
    get_available_slots,
    appointment_detail,
    update_appointment_status,
    cancel_appointment,
)
from .dashboards import (
    doctor_dashboard,
    receptionist_dashboard,
    nurse_dashboard,
    pharmacy_dashboard,
)
from .leave import (
    doctor_leave_request,
    doctor_leave_history,
    cancel_leave_request,
    admin_leave_requests,
    review_leave_request,
)
from .availability import (
    manage_availability,
    delete_availability,
)
from .inquiries import (
    inquiry_list,
    appointment_inquiry_detail,
    contact_inquiry_detail,
    mark_inquiries_seen,
)
from .notifications import (
    get_notifications,
    mark_inquiry_seen,
    mark_email_reply_seen,
)

__all__ = [
    "appointment_list",
    "book_appointment",
    "get_available_slots",
    "appointment_detail",
    "update_appointment_status",
    "cancel_appointment",
    "doctor_dashboard",
    "receptionist_dashboard",
    "nurse_dashboard",
    "pharmacy_dashboard",
    "doctor_leave_request",
    "doctor_leave_history",
    "cancel_leave_request",
    "admin_leave_requests",
    "review_leave_request",
    "manage_availability",
    "delete_availability",
    "inquiry_list",
    "appointment_inquiry_detail",
    "contact_inquiry_detail",
    "mark_inquiries_seen",
    "get_notifications",
    "mark_inquiry_seen",
    "mark_email_reply_seen",
]
