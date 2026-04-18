from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import render
from .models import Student, Announcement, FeePayment, ExamResult


# --- CUSTOM PRINT ACTIONS ---

def print_as_register(modeladmin, request, queryset):
    """Prints a professional student register based on current selection/filter"""
    return render(request, 'portal/print_student_list.html', {
        'students': queryset.order_by('full_name'),
        'user': request.user
    })


print_as_register.short_description = "🖨️ Print Selected as Register"


def print_academic_report(modeladmin, request, queryset):
    """Prints a mark sheet for selected exam results"""
    first_record = queryset.first()
    return render(request, 'portal/print_marks_list.html', {
        'results': queryset.select_related('student'),
        'unit_code': first_record.unit_code if first_record else "N/A",
        'subject_name': first_record.subject_name if first_record else "N/A",
        'user': request.user
    })


print_academic_report.short_description = "📊 Print Academic Mark Sheet"


# --- PROXY MODELS FOR SIDEBAR ORGANIZATION ---

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
    # display gender and semester for quick view
    list_display = ('admission_number', 'full_name', 'gender', 'semester', 'school', 'get_fee_status', 'is_active')

    # Comprehensive filtering: School, Semester, Gender, and Fee Status
    list_filter = ('school', 'semester', 'gender', 'is_active', 'fee_balance')

    search_fields = ('full_name', 'admission_number', 'id_number', 'phone_number')
    actions = [print_as_register, 'reset_passwords_to_id']

    def get_fee_status(self, obj):
        if obj.fee_balance > 0:
            return format_html('<b style="color: #b91c1c;">OWING: {}</b>', obj.fee_balance)
        return format_html('<b style="color: #15803d;">CLEARED</b>')

    get_fee_status.short_description = "Accounting"

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=False, is_superuser=False)

    def reset_passwords_to_id(self, request, queryset):
        for user in queryset:
            user.set_password(user.id_number)
            user.save()
        self.message_user(request, f"Passwords for {queryset.count()} users reset to their ID Numbers.")

    reset_passwords_to_id.short_description = "🔐 Reset Passwords to ID Number"


@admin.register(StaffUser)
class StaffUserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'school', 'phone_number', 'id_number', 'is_active')
    list_filter = ('school', 'is_active')
    search_fields = ('full_name', 'phone_number')
    actions = [print_as_register, 'reset_passwords_to_id']

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=True, is_superuser=False)


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject_name', 'unit_code', 'marks', 'grade', 'classification', 'is_published')

    # Filter by Grade (Distinction/Pass), Semester, and Publication status
    list_filter = ('grade', 'classification', 'semester', 'is_published', 'student__school')

    list_editable = ('is_published', 'marks')
    search_fields = ('student__full_name', 'unit_code', 'subject_name')
    actions = [print_academic_report, 'publish_marks', 'unpublish_marks']

    def publish_marks(self, request, queryset):
        queryset.update(is_published=True)

    publish_marks.short_description = "✅ Mark as Published (Visible to Students)"

    def unpublish_marks(self, request, queryset):
        queryset.update(is_published=False)

    unpublish_marks.short_description = "🚫 Mark as Draft (Hide from Students)"


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('reference_code', 'student', 'amount', 'method', 'date_paid')
    search_fields = ('reference_code', 'student__full_name', 'student__admission_number')
    list_filter = ('method', 'date_paid')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'audience', 'is_priority', 'date_posted')
    list_filter = ('audience', 'is_priority')
    list_editable = ('is_priority', 'audience')
    search_fields = ('title', 'content')