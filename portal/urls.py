from django.urls import path
from . import views

urlpatterns = [
    # --- Authentication ---
    path('login/', views.portal_login, name='portal_login'),
    path('logout/', views.portal_logout, name='portal_logout'),

    # --- Student Dashboard & Profile ---
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('update-photo/', views.update_photo, name='update_photo'),
    path('delete-photo/', views.delete_photo, name='delete_photo'),

    # --- Financials ---
    path('financials/', views.student_financials, name='student_financials'),

    # --- Academics & Results ---
    path('academics/', views.academic_units, name='academics'),
    path('results/', views.exam_results, name='exam_results'),

    # --- Transcript & Printing ---
    # This renders the official transcript.html (restricted by fee_balance in views)
    path('transcript/', views.view_transcript, name='view_transcript'),

    # Optional: For the Admin "Print All" functionality we added in admin.py
    # path('print-reports/', views.admin_print_reports, name='admin_print_reports'),
]