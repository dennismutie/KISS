from django.shortcuts import render

# Home Page View
def home_view(request):
    return render(request, 'home.html')

# About Us View
def about_view(request):
    return render(request, 'about.html')

# Programs View
def programs_view(request):
    return render(request, 'programs.html')

# Short Courses View
def short_courses_view(request):
    return render(request, 'short_courses.html')

# Admission/Application View
def admission_view(request):
    return render(request, 'admissions.html')

# FAQ View
def faq_view(request):
    return render(request, 'FAQ.html')

# Contact Us View
def contact_view(request):
    # Logic for handling contact form POST requests can go here
    return render(request, 'contact.html')