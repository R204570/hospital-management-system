from django.urls import path
from . import views

urlpatterns = [
    # Dashboard URLs
    path('receptionist-dashboard/', views.receptionist_dashboard, name='receptionist_dashboard'),
    path('doctor-dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('nurse-dashboard/', views.nurse_dashboard, name='nurse_dashboard'),
    path('pharmacy-dashboard/', views.pharmacy_dashboard, name='pharmacy_dashboard'),
    
    # Appointment Management
    path('book/', views.book_appointment, name='book_appointment'),
    path('list/', views.appointment_list, name='appointment_list'),
    path('detail/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('<int:pk>/update-status/', views.update_appointment_status, name='update_appointment_status'),
    path('cancel/<int:pk>/', views.cancel_appointment, name='cancel_appointment'),
    
    # AJAX views
    path('get-available-slots/', views.get_available_slots, name='get_available_slots'),
    
    # Doctor Availability Management
    path('availability/manage/', views.manage_availability, name='manage_availability'),
    path('availability/delete/<int:pk>/', views.delete_availability, name='delete_availability'),
    
    # Doctor Leave System
    path('leave-request/', views.doctor_leave_request, name='doctor_leave_request'),
    path('leave-history/', views.doctor_leave_history, name='doctor_leave_history'),
    path('admin-leave-requests/', views.admin_leave_requests, name='admin_leave_requests'),
    path('review-leave-request/<int:pk>/', views.review_leave_request, name='review_leave_request'),
    path('cancel-leave-request/<int:pk>/', views.cancel_leave_request, name='cancel_leave_request'),
    
    # Inquiry Management URLs
    path('inquiries/', views.inquiry_list, name='inquiry_list'),
    path('inquiry/appointment/<int:inquiry_id>/', views.appointment_inquiry_detail, name='appointment_inquiry_detail'),
    path('inquiry/contact/<int:inquiry_id>/', views.contact_inquiry_detail, name='contact_inquiry_detail'),
    path('inquiries/mark-seen/', views.mark_inquiries_seen, name='mark_inquiries_seen'),
    
    # Notification API endpoints
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('mark-inquiry-seen/', views.mark_inquiry_seen, name='mark_inquiry_seen'),
    path('mark-email-reply-seen/', views.mark_email_reply_seen, name='mark_email_reply_seen'),
] 