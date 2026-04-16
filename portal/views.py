import os
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Announcement, FeePayment, ExamResult


# --- AUTHENTICATION ---

def portal_login(request):
    if request.method == "POST":
        phone = request.POST.get('phone')
        id_no = request.POST.get('password')

        user = authenticate(request, username=phone, password=id_no)

        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('/admin/')
            return redirect('student_dashboard')
        else:
            messages.error(request, "Invalid Phone Number or ID Number")

    return render(request, 'portal/login.html')


def portal_logout(request):
    logout(request)
    return redirect('portal_login')


# --- DASHBOARD ---

def student_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('portal_login')

    announcements = Announcement.objects.all().order_by('-date_posted')
    return render(request, 'portal/dashboard.html', {'announcements': announcements})


# --- FINANCIALS ---

def student_financials(request):
    if not request.user.is_authenticated:
        return redirect('portal_login')

    payments = FeePayment.objects.filter(student=request.user).order_by('-date_paid')

    context = {
        'payments': payments,
        'balance': request.user.fee_balance
    }
    return render(request, 'portal/financials.html', context)


# --- ACADEMICS ---

def academic_units(request):
    if not request.user.is_authenticated:
        return redirect('portal_login')

    return render(request, 'portal/academics.html', {'student': request.user})


# --- RESULTS & TRANSCRIPT (FEES RESTRICTED) ---

def exam_results(request):
    if not request.user.is_authenticated:
        return redirect('portal_login')

    # 🛑 FEE CHECK: Only allow access if balance is 0 or less
    if request.user.fee_balance > 0:
        messages.warning(request,
                         f"Access Denied: Please clear your balance of KSh {request.user.fee_balance} to view exam results.")
        return redirect('student_financials')

    results = ExamResult.objects.filter(student=request.user).order_by('semester')
    return render(request, 'portal/results.html', {'results': results})


def view_transcript(request):
    if not request.user.is_authenticated:
        return redirect('portal_login')

    # 🛑 FEE CHECK: Prevent printing/viewing transcript if fees are owed
    if request.user.fee_balance > 0:
        messages.error(request, "Transcript generation blocked. Please clear your fee balance first.")
        return redirect('student_financials')

    # Fetch all academic history for the transcript
    results = ExamResult.objects.filter(student=request.user).order_by('semester')

    context = {
        'results': results,
        'student': request.user,
    }
    return render(request, 'portal/transcript.html', context)


# --- PHOTO MANAGEMENT ---

def update_photo(request):
    if not request.user.is_authenticated:
        return redirect('portal_login')

    if request.method == "POST" and request.FILES.get('photo'):
        student = request.user
        if student.profile_photo and student.profile_photo.name != 'students/default.png':
            if os.path.exists(student.profile_photo.path):
                os.remove(student.profile_photo.path)

        student.profile_photo = request.FILES['photo']
        student.save()
        messages.success(request, "Profile photo updated successfully!")
    return redirect('student_dashboard')


def delete_photo(request):
    if not request.user.is_authenticated:
        return redirect('portal_login')

    student = request.user
    if student.profile_photo and student.profile_photo.name != 'students/default.png':
        if os.path.exists(student.profile_photo.path):
            os.remove(student.profile_photo.path)

    student.profile_photo = 'students/default.png'
    student.save()
    messages.success(request, "Profile photo removed.")
    return redirect('student_dashboard')