from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import render
from django.urls import reverse
from .models import Student, Announcement, FeePayment, ExamResult


# --- CUSTOM PRINT ACTIONS ---

def print_as_register(modeladmin, request, queryset):
    """Prints a professional student register based on current selection/filter"""
    return render(request, 'portal/print_student_list.html', {
        'students': queryset,
        'user': request.user
    })


print_as_register.short_description = "🖨️ Print Selected as Register"


def print_academic_report(modeladmin, request, queryset):
    """Prints a mark sheet for selected exam results"""
    # Group by unit code if printing marks
    return render(request, 'portal/print_marks_list.html', {
        'results': queryset,
        'unit_code': queryset.first().unit_code if queryset.exists() else "N/A",
        'subject_name': queryset.first().subject_name if queryset.exists() else "N/A",
        'user': request.user
    })


print_academic_report.short_description = "📊 Print Academic Mark Sheet"


# --- PROXY MODELS ---

class StudentUser(Student):
    class Meta:
        proxy = True
        verbose_name = "Student"
        verbose_name_plural = "1. Students"


class StaffUser(Student):
    class Meta:
        proxy = True
        verbose_name = "Staff Member"
        verbose_name_plural = "2. Staff & Lecturers"


# --- ADMIN CLASSES ---

@admin.register(StudentUser)
class StudentUserAdmin(admin.ModelAdmin):
    # Added 'gender' and 'semester' assuming they exist in your Student model
    list_display = ('admission_number', 'full_name', 'school', 'fee_balance', 'get_status_badge', 'is_active')
    list_filter = ('school', 'semester', 'gender', 'is_active', 'fee_balance')
    search_fields = ('full_name', 'admission_number', 'id_number')
    actions = [print_as_register, 'reset_passwords_to_id']

    def get_status_badge(self, obj):
        if obj.fee_balance > 0:
            return format_html('<span style="color: red;">OWING</span>')
        return format_html('<span style="color: green;">CLEARED</span>')

    get_status_badge.short_description = "Fin Status"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=False, is_superuser=False)

    def reset_passwords_to_id(self, request, queryset):
        for user in queryset:
            user.set_password(user.id_number)
            user.save()
        self.message_user(request, "Passwords reset to ID Numbers.")


@admin.register(StaffUser)
class StaffUserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'school', 'phone_number', 'is_staff', 'is_active')
    list_filter = ('school', 'is_active')
    actions = [print_as_register]  # Can print a staff list too

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=True, is_superuser=False)


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject_name', 'unit_code', 'marks', 'grade', 'is_published', 'date_entered')
    list_filter = ('is_published', 'grade', 'semester', 'student__school')
    list_editable = ('is_published',)  # Quick verify directly from the list!
    actions = [print_academic_report, 'verify_marks']
    search_fields = ('student__full_name', 'unit_code')

    def verify_marks(self, request, queryset):
        queryset.update(is_published=True)
        self.message_user(request, "Selected marks have been approved and published to students.")

    verify_marks.short_description = "✅ Approve & Publish Selected Marks"


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'audience', 'is_priority', 'date_posted')
    list_editable = ('is_priority',)
    # Priority announcements show up with a Red Badge/Pulse in the user dashboard