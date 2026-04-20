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

    # --- Session Reporting (Progress Bar Logic) ---
    path('session-reporting/', views.session_reporting, name='session_reporting'),

    # --- Transcript System (The Split) ---
    # 1. Internal Semester Report (No QR, needs cleared fees)
    path('transcript/semester/', views.semester_transcript, name='semester_transcript'),

    # 2. Official Leaving Transcript (QR Code, needs Admin approval)
    path('transcript/official/<str:id_number>/', views.official_leaving_transcript, name='official_leaving_transcript'),

    # # 3. Public Verification (Destination for the Scanned QR Code)
    # path('verify/<str:id_number>/', views.verify_transcript_public, name='verify_transcript_public'),

    # --- Staff Portal ---
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/mark-entry/', views.bulk_mark_entry, name='bulk_mark_entry'),

    # --- Printing & Reports ---
    path('print/student-list/', views.print_student_list, name='print_student_list'),
    path('print-reports/', views.print_student_list, name='admin_print_reports'),
    path('print-marks/<str:unit_code>/', views.print_marks_list, name='print_marks_list'),
]