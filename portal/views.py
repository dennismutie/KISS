import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Announcement, FeePayment, ExamResult, Student


# --- AUTHENTICATION ---

def portal_login(request):
    if request.method == "POST":
        phone = request.POST.get('phone')
        id_no = request.POST.get('password')

        user = authenticate(request, username=phone, password=id_no)

        if user is not None:
            login(request, user)

            # Admin & Lecturers both use the Staff Dashboard for marks entry
            if user.is_superuser or user.is_staff:
                return redirect('staff_dashboard')

            # Student Redirect
            return redirect('student_dashboard')
        else:
            messages.error(request, "Invalid Phone Number or ID Number")

    return render(request, 'portal/login.html')


def portal_logout(request):
    logout(request)
    return redirect('portal_login')


# --- STUDENT VIEWS ---

def student_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('portal_login')

    # Redirect privileged users away from student layout
    if request.user.is_staff or request.user.is_superuser:
        return redirect('staff_dashboard')

    all_announcements = Announcement.objects.all().order_by('-date_posted')
    announcements = [
        a for a in all_announcements
        if getattr(a, 'audience', 'ALL') in ['ALL', 'STUDENTS']
    ]

    return render(request, 'portal/dashboard.html', {'announcements': announcements})


def student_financials(request):
    if not request.user.is_authenticated:
        return redirect('portal_login')

    payments = FeePayment.objects.filter(student=request.user).order_by('-date_paid')
    context = {
        'payments': payments,
        'balance': request.user.fee_balance
    }
    return render(request, 'portal/financials.html', context)


def exam_results(request):
    if not request.user.is_authenticated:
        return redirect('portal_login')

    if request.user.fee_balance > 0:
        messages.warning(request, f"Access Denied: Please clear your balance of KSh {request.user.fee_balance}.")
        return redirect('student_financials')

    # Now fetching all results directly since is_published defaults to True
    results = ExamResult.objects.filter(student=request.user, is_published=True).order_by('semester')

    return render(request, 'portal/results.html', {'results': results})


def view_transcript(request):
    if not request.user.is_authenticated:
        return redirect('portal_login')

    if request.user.fee_balance > 0:
        messages.error(request, "Transcript blocked. Please clear your fee balance first.")
        return redirect('student_financials')

    # Direct access to published results
    results = ExamResult.objects.filter(student=request.user, is_published=True).order_by('semester')

    context = {'results': results, 'student': request.user}
    return render(request, 'portal/transcript.html', context)


# --- STAFF / LECTURER VIEWS ---

def staff_dashboard(request):
    # BOTH Superusers and Staff can manage marks here
    if not request.user.is_authenticated or (not request.user.is_staff and not request.user.is_superuser):
        return redirect('portal_login')

    all_announcements = Announcement.objects.all().order_by('-date_posted')
    announcements = [
        a for a in all_announcements
        if getattr(a, 'audience', 'ALL') in ['ALL', 'STAFF']
    ]

    if request.user.is_superuser:
        my_students = Student.objects.filter(is_staff=False, is_superuser=False).order_by('full_name')
    else:
        my_students = Student.objects.filter(school=request.user.school, is_staff=False).order_by('full_name')

    context = {
        'announcements': announcements,
        'my_students': my_students
    }
    return render(request, 'portal/staff_dashboard.html', context)


def bulk_mark_entry(request):
    # Allow Superusers and Staff to enter marks
    if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
        return redirect('portal_login')

    if request.user.is_superuser:
        students = Student.objects.filter(is_staff=False, is_superuser=False).order_by('full_name')
    else:
        students = Student.objects.filter(school=request.user.school, is_staff=False).order_by('full_name')

    if request.method == "POST":
        sub_name = request.POST.get('subject_name')
        u_code = request.POST.get('unit_code')
        sem = request.POST.get('semester')

        if not sub_name or not u_code:
            messages.error(request, "Subject Name and Unit Code are required!")
            return render(request, 'portal/bulk_mark_entry.html', {'students': students})

        count = 0
        for student in students:
            mark_value = request.POST.get(f'marks_{student.id}')

            if mark_value and mark_value.strip():
                # Direct entry: is_published is set to True automatically
                ExamResult.objects.create(
                    student=student,
                    subject_name=sub_name,
                    unit_code=u_code,
                    marks=int(mark_value),
                    semester=sem,
                    entered_by=request.user,
                    is_published=True  # Reflects immediately
                )
                count += 1

        messages.success(request, f"Successfully committed {count} marks for {sub_name}.")
        return redirect('staff_dashboard')

    return render(request, 'portal/bulk-mark_entry.html', {'students': students})


# --- PHOTO MANAGEMENT ---

def update_photo(request):
    if not request.user.is_authenticated:
        return redirect('portal_login')

    if request.method == "POST" and request.FILES.get('photo'):
        user = request.user
        if user.profile_photo and 'lec.png' not in user.profile_photo.name:
            if os.path.exists(user.profile_photo.path):
                os.remove(user.profile_photo.path)

        user.profile_photo = request.FILES['photo']
        user.save()
        messages.success(request, "Profile photo updated successfully!")

    if request.user.is_superuser or request.user.is_staff:
        return redirect('staff_dashboard')
    return redirect('student_dashboard')


def delete_photo(request):
    if not request.user.is_authenticated:
        return redirect('portal_login')

    user = request.user
    if user.profile_photo and 'lec.png' not in user.profile_photo.name:
        if os.path.exists(user.profile_photo.path):
            os.remove(user.profile_photo.path)

    user.profile_photo = 'students/lec.png'
    user.save()
    messages.success(request, "Profile photo removed.")

    if request.user.is_superuser or request.user.is_staff:
        return redirect('staff_dashboard')
    return redirect('student_dashboard')


# --- UTILITIES ---

def print_student_list(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('portal_login')

    if request.user.is_superuser:
        students = Student.objects.filter(is_staff=False, is_superuser=False)
    else:
        students = Student.objects.filter(school=request.user.school, is_staff=False)

    return render(request, 'portal/print_student_list.html', {'students': students.order_by('full_name')})


def academic_units(request):
    if not request.user.is_authenticated or request.user.is_staff:
        return redirect('portal_login')

    return render(request, 'portal/academics.html', {'student': request.user})


def print_marks_list(request, unit_code):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('portal_login')

    results = ExamResult.objects.filter(unit_code=unit_code)

    if not request.user.is_superuser:
        results = results.filter(student__school=request.user.school)

    results = results.select_related('student').order_by('student__full_name')

    if not results:
        messages.warning(request, f"No marks found for Unit Code: {unit_code}")
        return redirect('staff_dashboard')

    context = {
        'results': results,
        'unit_code': unit_code,
        'subject_name': results[0].subject_name,
        'count': results.count()
    }
    return render(request, 'portal/print_marks_list.html', context)