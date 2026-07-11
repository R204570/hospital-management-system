"""Forms package for the website app (split by feature).

Every view is re-exported so ``from . import views`` and
``website.forms.<name>`` keep working unchanged.
"""
from .blog import (
    BlogForm,
    BlogSubscriptionForm,
    BlogCommentForm,
    BlogSearchForm,
)
from .inquiries import (
    ContactInquiryForm,
    AppointmentInquiryForm,
)

__all__ = [
    "BlogForm",
    "BlogSubscriptionForm",
    "BlogCommentForm",
    "BlogSearchForm",
    "ContactInquiryForm",
    "AppointmentInquiryForm",
]
