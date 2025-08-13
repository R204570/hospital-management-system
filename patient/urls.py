from django.urls import path
from . import views

urlpatterns = [
    # Patient management
    path('list/', views.patient_list, name='patient_list'),
    path('register/', views.patient_register, name='patient_register'),
    path('<int:pk>/', views.patient_detail, name='patient_detail'),
    path('<int:pk>/update/', views.patient_update, name='patient_update'),
    
    # Medical records
    path('medical-record/create/', views.create_medical_record, name='create_medical_record'),
    path('medical-record/create/<int:patient_id>/', views.create_medical_record, name='create_medical_record'),
    path('medical-record/create/appointment/<int:appointment_id>/', views.create_medical_record, name='create_medical_record_from_appointment'),
    path('medical-record/<int:record_id>/', views.view_medical_record, name='view_medical_record'),
    path('medical-record/<int:record_id>/update/', views.update_medical_record, name='update_medical_record'),
    path('medical-record/<int:record_id>/pdf/', views.medical_record_pdf, name='medical_record_pdf'),
    path('medical-record/<int:record_id>/delete/', views.delete_medical_record, name='delete_medical_record'),
    
    # Medical sidebar functionality
    path('assigned-patients/', views.assigned_patients, name='assigned_patients'),
    path('recent-medical-records/', views.recent_medical_records, name='recent_medical_records'),
    path('pdf-reports/', views.pdf_reports, name='pdf_reports'),
    path('patient-statistics/', views.patient_statistics, name='patient_statistics'),
    
    # Room management
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/create/', views.room_create, name='room_create'),
    path('rooms/<int:pk>/', views.room_detail, name='room_detail'),
    path('rooms/<int:pk>/update/', views.room_update, name='room_update'),
    
    # Bed management
    path('beds/', views.bed_list, name='bed_list'),
    path('beds/create/', views.bed_create, name='bed_create'),
    path('beds/create/<int:room_id>/', views.bed_create, name='bed_create_for_room'),
    path('beds/<int:pk>/update/', views.bed_update, name='bed_update'),
    
    # Patient admission
    path('admissions/', views.admission_list, name='admission_list'),
    path('admissions/create/', views.admission_create, name='admission_create'),
    path('admissions/create/<int:patient_id>/', views.admission_create, name='admission_create_for_patient'),
    path('admissions/<int:pk>/', views.admission_detail, name='admission_detail'),
    path('admissions/<int:pk>/discharge/', views.admission_discharge, name='admission_discharge'),
    path('admissions/emergency/', views.emergency_admission, name='emergency_admission'),
    
    # Nurse prescription management
    path('nurse/prescriptions/', views.nurse_prescription_list, name='nurse_prescription_list'),
    path('nurse/prescriptions/<int:pk>/', views.nurse_prescription_detail, name='nurse_prescription_detail'),
    path('nurse/prescriptions/<int:record_id>/administer/', views.nurse_medication_administration, name='nurse_medication_administration'),
    
    # Admission request management
    path('admission-requests/', views.admission_request_list, name='admission_request_list'),
    path('admission-requests/create/', views.admission_request_create, name='admission_request_create'),
    path('admission-requests/create/<int:patient_id>/', views.admission_request_create, name='admission_request_create_for_patient'),
    path('admission-requests/<int:pk>/', views.admission_request_detail, name='admission_request_detail'),
    path('admission-requests/<int:pk>/process/', views.admission_request_process, name='admission_request_process'),
    path('admission-requests/<int:pk>/assign-room/', views.admission_request_assign_room, name='admission_request_assign_room'),

    # AJAX search endpoints
    path('api/patients/search/', views.patient_search_api, name='patient_search_api'),
    path('api/beds/search/', views.bed_search_api, name='bed_search_api'),
] 