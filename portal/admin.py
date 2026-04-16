from django.contrib import admin
from django.utils.html import format_html
from .models import Student, Announcement, FeePayment, ExamResult


# --- INLINES ---

class FeePaymentInline(admin.TabularInline):
    model = FeePayment
    extra = 0  # Don't clutter the page with empty rows
    readonly_fields = ('date_paid',)  # Prevent accidental back-dating
    classes = ['collapse']  # Keeps the page neat, admin can expand if needed


class ExamResultInline(admin.TabularInline):
    model = ExamResult
    extra = 0
    fields = ('subject_name', 'unit_code', 'marks', 'grade', 'semester')
    readonly_fields = ('grade',)  # Auto-calculated by model
    classes = ['collapse']


# --- MODEL ADMINS ---

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    # Professional list view with colored balance status
    list_display = ('admission_number', 'full_name', 'phone_number', 'school', 'course', 'get_balance_status',
                    'is_active')
    search_fields = ('full_name', 'phone_number', 'id_number', 'admission_number')
    list_filter = ('school', 'is_staff', 'is_active')
    actions = ['print_student_reports']  # Custom Print Action

    # Organizing the Edit Page into sharp sections
    fieldsets = (
        ('Personal Information', {
            'fields': ('full_name', 'phone_number', 'id_number', 'profile_photo')
        }),
        ('Academic Records', {
            'fields': ('admission_number', 'school', 'course')
        }),
        ('Financial Status', {
            'fields': ('fee_balance',),
            'description': '<b>Note:</b> Balance is auto-calculated when payments are added below.'
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups'),
            'classes': ('collapse',)
        }),
    )

    inlines = [FeePaymentInline, ExamResultInline]

    # Visual Fee Status (Red if owing, Green if cleared)
    def get_balance_status(self, obj):
        if obj.fee_balance > 0:
            return format_html('<b style="color: #991b1b;">KSh {} (Owing)</b>', obj.fee_balance)
        elif obj.fee_balance < 0:
            return format_html('<b style="color: #166534;">KSh {} (Credit)</b>', abs(obj.fee_balance))
        return format_html('<b style="color: #166534;">Cleared</b>')

    get_balance_status.short_description = "Fee Balance"

    # Custom Action to "Print Details"
    def print_student_reports(self, request, queryset):
        # In a real Django setup, you'd redirect to a specific URL that generates a PDF or Print view
        # For now, this prepares the admin to know which students to "Report" on
        from django.http import HttpResponseRedirect
        from django.urls import reverse

        # We can pass the IDs to a custom print view we create
        selected = queryset.values_list('pk', flat=True)
        return HttpResponseRedirect(f"/portal/print-reports/?ids={','.join(map(str, selected))}")

    print_student_reports.short_description = "🖨️ Print Selected Student Reports"


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject_name', 'unit_code', 'marks', 'grade', 'semester')
    list_filter = ('semester', 'grade', 'student__school')
    search_fields = ('student__full_name', 'subject_name', 'unit_code')


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('reference_code', 'student', 'amount', 'method', 'date_paid')
    search_fields = ('reference_code', 'student__full_name')
    list_filter = ('method', 'date_paid')

    # Allows admin to quickly see student's current total debt when adding a payment
    readonly_fields = ('get_current_balance',)

    def get_current_balance(self, obj):
        return f"KSh {obj.student.fee_balance}"

    get_current_balance.short_description = "Student's Current Balance"


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_priority', 'date_posted')
    list_editable = ('is_priority',)  # Can toggle priority directly from the list
    search_fields = ('title',)