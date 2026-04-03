from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
path('home/', views.home_view, name='home'),
    path('programs/', views.programs_view, name='programs'),
    path('shortcourses/', views.short_courses_view, name='shortcourses'),
    path('admissions/', views.admission_view, name='admission'),
    path('FAQ/', views.faq_view, name='FAQ'),
    path('contact/', views.contact_view, name='contact'),
]