from django.urls import path
from . import views

urlpatterns = [
    # --- Authentication ---
    path('login/', views.portal_login, name='portal_login'),
    path('logout/', views.portal_logout, name='portal_logout'),

    # --- Shared Profile Features ---
    path('update-photo/', views.update_photo, name='update_photo'),
    path('delete-photo/', views.delete_photo, name='delete_photo'),

    # --- Student Portal ---
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('financials/', views.student_financials, name='student_financials'),
    path('academics/', views.academic_units, name='academics'),
    path('results/', views.exam_results, name='exam_results'),
    path('transcript/', views.view_transcript, name='view_transcript'),

    # --- Staff Portal (New) ---
    # Main landing for lecturers
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),

    # The bulk entry page for marks
    path('staff/mark-entry/', views.bulk_mark_entry, name='bulk_mark_entry'),

    # --- Printing & Reports (New) ---
    # General student list for staff/admin to print
    path('print/student-list/', views.print_student_list, name='print_student_list'),

    # Handling the 'Print Selected' redirect from Django Admin
    path('print-reports/', views.print_student_list, name='admin_print_reports'),

path('print-marks/<str:unit_code>/', views.print_marks_list, name='print_marks_list'),
]