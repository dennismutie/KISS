import os
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from .models import Announcement, FeePayment, ExamResult, Student

# --- AUTHENTICATION ---

def portal_login(request):
    """Secure login handling with session cleanup"""
    if request.user.is_authenticated:
        logout(request)

    if request.method == "POST":
        phone = request.POST.get('phone')
        id_no = request.POST.get('password')
        user = authenticate(request, username=phone, password=id_no)

        if user is not None:
            login(request, user)
            if user.is_superuser or user.is_staff:
                return redirect('staff_dashboard')
            return redirect('student_dashboard')
        else:
            messages.error(request, "Invalid Phone Number or ID Number")
    return render(request, 'portal/login.html')

def portal_logout(request):
    logout(request)
    return redirect('portal_login')

# --- STUDENT PORTAL & PROGRESS LOGIC ---

def student_dashboard(request):
    """Main student landing with dynamic progress bar calculation"""
    if not request.user.is_authenticated or request.user.is_staff:
        return redirect('portal_login')

    progress = 0
    if request.user.session_start_date and request.user.session_end_date:
        today = date.today()
        if today >= request.user.session_start_date:
            total_days = (request.user.session_end_date - request.user.session_start_date).days
            elapsed_days = (today - request.user.session_start_date).days
            if total_days > 0:
                progress = int((elapsed_days / total_days) * 100)
                progress = min(max(progress, 0), 100)

    all_announcements = Announcement.objects.all().order_by('-date_posted')
    announcements = [a for a in all_announcements if getattr(a, 'audience', 'ALL') in ['ALL', 'STUDENTS']]

    context = {
        'announcements': announcements,
        'semester_progress': progress,
        'current_semester_name': f"{request.user.semester} 2025/2026"
    }
    return render(request, 'portal/dashboard.html', context)

def session_reporting(request):
    """Updates model to start a new 4-month tracking session"""
    if not request.user.is_authenticated:
        return redirect('portal_login')

    user = request.user
    user.session_reported = True
    user.session_start_date = date.today()
    user.session_end_date = date.today().replace(month=(date.today().month + 4) % 12 or 12)
    user.save()

    messages.success(request, f"Reporting successful! Your progress tracker is now active for {user.semester}.")
    return redirect('student_dashboard')

# --- TRANSCRIPT SYSTEM (CLEAN VERSION) ---

def semester_transcript(request):
    """Internal report card - Requires zero balance"""
    if not request.user.is_authenticated:
        return redirect('portal_login')

    if request.user.fee_balance > 0:
        messages.warning(request, "Access Denied: Please clear your fee balance to view your semester report.")
        return redirect('student_financials')

    results = ExamResult.objects.filter(student=request.user, is_published=True).order_by('semester')
    return render(request, 'portal/transcript.html', {'results': results, 'student': request.user})

def official_leaving_transcript(request, id_number):
    """Official transcript - No QR code, Admin-controlled access"""
    student = get_object_or_404(Student, id_number=id_number)

    # Security Gate: Only Admins can access, or student if officially ISSUED
    if not request.user.is_staff and not request.user.is_superuser:
        if request.user.id_number != id_number or student.official_transcript_status != 'ISSUED':
            messages.error(request, "Official Transcript not yet available. Please contact the Registrar.")
            return redirect('student_dashboard')

    results = ExamResult.objects.filter(student=student, is_published=True).order_by('semester')

    return render(request, 'portal/official_transcript.html', {
        'student': student,
        'results': results
    })

# --- PHOTO MANAGEMENT (With 2MB Limit) ---

def update_photo(request):
    if not request.user.is_authenticated:
        return redirect('portal_login')

    if request.method == "POST" and request.FILES.get('photo'):
        photo = request.FILES['photo']

        if photo.size > 2 * 1024 * 1024:
            messages.error(request, "Error: Profile photo must be smaller than 2MB.")
            return redirect('student_dashboard')

        user = request.user
        if user.profile_photo and 'lec.png' not in user.profile_photo.name:
            if os.path.exists(user.profile_photo.path):
                os.remove(user.profile_photo.path)

        user.profile_photo = photo
        user.save()
        messages.success(request, "Profile photo updated successfully!")

    return redirect('staff_dashboard' if request.user.is_staff else 'student_dashboard')

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

    return redirect('staff_dashboard' if request.user.is_staff else 'student_dashboard')

# --- STAFF / LECTURER VIEWS ---

def staff_dashboard(request):
    if not request.user.is_authenticated or (not request.user.is_staff and not request.user.is_superuser):
        return redirect('portal_login')

    all_announcements = Announcement.objects.all().order_by('-date_posted')
    announcements = [a for a in all_announcements if getattr(a, 'audience', 'ALL') in ['ALL', 'STAFF']]

    if request.user.is_superuser:
        my_students = Student.objects.filter(is_staff=False, is_superuser=False).order_by('full_name')
    else:
        my_students = Student.objects.filter(school=request.user.school, is_staff=False).order_by('full_name')

    context = {'announcements': announcements, 'my_students': my_students}
    return render(request, 'portal/staff_dashboard.html', context)

def bulk_mark_entry(request):
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

        count = 0
        for student in students:
            mark_value = request.POST.get(f'marks_{student.id}')
            if mark_value and mark_value.strip():
                ExamResult.objects.create(
                    student=student, subject_name=sub_name, unit_code=u_code,
                    marks=int(mark_value), semester=sem, entered_by=request.user, is_published=True
                )
                count += 1
        messages.success(request, f"Bulk Entry: Committed {count} marks for {sub_name}.")
        return redirect('staff_dashboard')

    return render(request, 'portal/bulk-mark_entry.html', {'students': students})

# --- UTILITIES & REPORTS ---

def student_financials(request):
    if not request.user.is_authenticated:
        return redirect('portal_login')
    payments = FeePayment.objects.filter(student=request.user).order_by('-date_paid')
    return render(request, 'portal/financials.html', {'payments': payments, 'balance': request.user.fee_balance})

def exam_results(request):
    if not request.user.is_authenticated:
        return redirect('portal_login')
    if request.user.fee_balance > 0:
        messages.warning(request, f"Access Blocked: Please clear KSh {request.user.fee_balance} outstanding balance.")
        return redirect('student_financials')
    results = ExamResult.objects.filter(student=request.user, is_published=True).order_by('semester')
    return render(request, 'portal/results.html', {'results': results})

def print_student_list(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('portal_login')
    students = Student.objects.filter(is_staff=False, is_superuser=False) if request.user.is_superuser else Student.objects.filter(school=request.user.school, is_staff=False)
    return render(request, 'portal/print_student_list.html', {'students': students.order_by('full_name')})

def academic_units(request):
    if not request.user.is_authenticated or request.user.is_staff:
        return redirect('portal_login')
    return render(request, 'portal/academics.html', {'student': request.user})

def print_marks_list(request, unit_code):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('portal_login')
    results = ExamResult.objects.filter(unit_code=unit_code).select_related('student').order_by('student__full_name')
    if not results: return redirect('staff_dashboard')
    return render(request, 'portal/print_marks_list.html', {'results': results, 'unit_code': unit_code, 'subject_name': results[0].subject_name})