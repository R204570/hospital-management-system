from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.contrib import messages
from django.conf import settings

class RoleBasedAccessMiddleware:
    """
    Middleware to ensure users can only access pages appropriate for their role.
    This adds a secondary layer of protection in addition to the view decorators.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Skip this check for unauthenticated users or login/logout pages
        if not request.user.is_authenticated or request.path in [reverse('login'), reverse('logout')]:
            return self.get_response(request)
            
        # Get current URL pattern name
        url_name = resolve(request.path).url_name
        
        # Check if the current user has access to this URL based on their role
        if not self.check_permission(request.user, url_name, request.path):
            messages.error(request, "You don't have permission to access this page.")
            return redirect('dashboard')  # Redirect to main dashboard for further routing
            
        # If all checks pass, continue with the request
        return self.get_response(request)
    
    def check_permission(self, user, url_name, path):
        """
        Check if a user has permission to access a specific URL based on their role.
        Returns True if access is allowed, False otherwise.
        """
        # Always allow access to common pages
        common_urls = ['dashboard', 'profile', 'change_password']
        if url_name in common_urls:
            return True
            
        # Define role-specific URL patterns
        admin_urls = ['admin_dashboard', 'user_list', 'create_user', 'update_user', 
                      'admin_leave_requests', 'review_leave_request', 'get_notifications', 'mark_inquiry_seen']
        doctor_urls = ['doctor_dashboard', 'manage_availability', 'delete_availability',
                       'doctor_leave_request', 'doctor_leave_history', 'cancel_leave_request',
                       # Add patient-related URLs for doctors
                       'patient_list', 'patient_detail', 'view_medical_record', 
                       'create_medical_record', 'update_medical_record', 'delete_medical_record',
                       'assigned_patients', 'recent_medical_records', 'medical_record_pdf',
                       # Add admission-related URLs for doctors
                       'admission_create', 'admission_create_for_patient', 'admission_detail',
                       'admission_list', 'admission_discharge', 'emergency_admission',
                       # Add blog management URLs for doctors
                       'my_blogs', 'create_blog', 'edit_blog', 'delete_blog', 'blog_detail']
        nurse_urls = ['nurse_dashboard', 'patient_list', 'patient_detail', 'view_medical_record',
                       # Add admission-related URLs for nurses
                       'admission_list', 'admission_detail', 'admission_create', 'emergency_admission',
                       # Add admission request URLs for nurses
                       'admission_request_list', 'admission_request_detail', 'admission_request_process',
                       'admission_request_assign_room',
                       # Add nurse prescription management URLs
                       'nurse_prescription_list', 'nurse_prescription_detail', 'nurse_medication_administration']
        receptionist_urls = ['receptionist_dashboard', 'book_appointment', 'cancel_appointment', 
                             'patient_list', 'patient_register', 'patient_update', 'patient_detail',
                             'inquiry_list', 'appointment_inquiry_detail', 'contact_inquiry_detail', 
                             'mark_inquiries_seen', 'get_notifications', 'mark_inquiry_seen', 'mark_email_reply_seen']
        pharmacist_urls = ['pharmacy_dashboard', 'medicine_list', 'medicine_detail', 'add_medicine', 
                           'edit_medicine', 'supplier_list', 'add_supplier', 'edit_supplier', 
                           'purchase_list', 'add_purchase', 'purchase_detail', 'receive_purchase', 
                           'cancel_purchase', 'sale_list', 'add_sale', 'sale_detail', 
                           'prescription_list', 'low_stock_list', 'expired_medicines']
            
        # Static files, admin, and media URLs are always accessible
        if (path.startswith(settings.STATIC_URL) or 
            path.startswith(settings.MEDIA_URL) or 
            path.startswith('/admin/')):
            return True
            
        # Allow access to website namespace URLs (public pages like blog, about, etc.)
        website_paths = ['/blog/', '/about/', '/contact/', '/doctors/', '/service/', '/appointment-inquiry/']
        if any(path.startswith(website_path) for website_path in website_paths):
            return True
            
        # Allow access to pharmacy URLs for pharmacists
        if user.role == 'PHARMACIST' and path.startswith('/pharmacy/'):
            return True
            
        # Check role-specific access
        if user.role == 'ADMIN' and url_name in admin_urls:
            return True
        elif user.role == 'DOCTOR' and url_name in doctor_urls:
            return True
        elif user.role == 'NURSE' and url_name in nurse_urls:
            return True
        elif user.role == 'RECEPTIONIST' and url_name in receptionist_urls:
            return True
        elif user.role == 'PHARMACIST' and url_name in pharmacist_urls:
            return True
            
        # For appointment_list and appointment_detail, we'll rely on the view-level permissions
        # since they implement custom filtering based on role
        if url_name in ['appointment_list', 'appointment_detail', 'update_appointment_status',
                        'get_available_slots']:
            return True
            
        # If we get here, deny access by default
        return False 