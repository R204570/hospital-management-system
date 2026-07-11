"""Views package for the website app (split by feature).

Every view is re-exported so ``from . import views`` and
``website.views.<name>`` keep working unchanged.
"""
from .pages import (
    index,
    about,
    contact,
    doctors,
    service,
    login_view,
    appointment,
    appointment_inquiry,
)
from .blog import (
    blog,
    blog_detail,
    create_blog,
    edit_blog,
    delete_blog,
    my_blogs,
    track_blog_view,
    delete_comment,
    subscribe_to_doctor,
)

__all__ = [
    "index",
    "about",
    "contact",
    "doctors",
    "service",
    "login_view",
    "appointment",
    "appointment_inquiry",
    "blog",
    "blog_detail",
    "create_blog",
    "edit_blog",
    "delete_blog",
    "my_blogs",
    "track_blog_view",
    "delete_comment",
    "subscribe_to_doctor",
]
