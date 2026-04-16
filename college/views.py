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
    return render(request, 'shortcourses.html')

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


def programs_view(request):
    # Get the search term from the URL (e.g., /programs/?search=Electrical)
    query = request.GET.get('search', '')

    # If you have a Course model, you would filter it here:
    # courses = Course.objects.filter(name__icontains=query) if query else Course.objects.all()

    context = {
        'search_query': query,
        # 'courses': courses,
    }
    return render(request, 'programs.html', context)
