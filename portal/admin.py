from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages
from django.db.models import Sum
from .models import Student, Announcement, FeePayment, ExamResult


# --- CUSTOM FORMS ---

class StaffUserForm(forms.ModelForm):
    """Custom form for Staff to allow multiple school selections"""
    school = forms.MultipleChoiceField(
        choices=Student.SCHOOL_CHOICES,
        widget=forms.SelectMultiple(attrs={'style': 'height: 150px;'}),
        help_text="Hold 'Ctrl' (Windows) or 'Command' (Mac) to select more than one school."
    )

    class Meta:
        model = Student
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing an existing staff, convert comma-separated string back to a list for the widget
        if self.instance and self.instance.school:
            self.initial['school'] = [s.strip() for s in self.instance.school.split(',')]

    def clean_school(self):
        # Convert the list from the widget into a clean comma-separated string for the DB
        data = self.cleaned_data.get('school')
        return ", ".join(data) if data else ""


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
    list_display = (
        'admission_number', 'full_name', 'school', 'semester',
        'get_total_course_cost', 'get_fee_status',
        'official_transcript_status', 'print_official_transcript'
    )
    list_filter = ('school', 'semester', 'gender', 'official_transcript_status', 'is_active')
    search_fields = ('full_name', 'admission_number', 'id_number', 'phone_number')

    fieldsets = (
        ('Personal Identity', {
            'fields': ('full_name', 'id_number', 'phone_number', 'gender', 'profile_photo')
        }),
        ('Academic Details', {
            'fields': ('school', 'course', 'semester', 'total_semesters', 'official_transcript_status')
        }),
        ('Financials (Dynamic)', {
            'fields': ('fees_per_semester',),
            'description': 'Fees are calculated dynamically based on semesters and payments.'
        }),
        ('System Status', {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'classes': ('collapse',),
        }),
    )

    actions = [print_as_register, 'issue_final_transcript', 'reset_passwords_to_id']

    def get_total_course_cost(self, obj):
        # Format number FIRST
        formatted_price = "{:,.2f}".format(obj.total_course_fees)
        # Use {} without the :.2f inside format_html
        return format_html('<span style="color: #64748b;">KES {}</span>', formatted_price)

    get_total_course_cost.short_description = "Total Cost"

    def get_fee_status(self, obj):
        balance = obj.fee_balance
        # Format the number as a string first to avoid SafeString errors
        formatted_balance = "{:,.2f}".format(abs(balance))

        if balance > 0:
            return format_html('<span style="color: #b91c1c; font-weight: bold;">OWING: {}</span>', formatted_balance)
        elif balance < 0:
            return format_html('<span style="color: #15803d; font-weight: bold;">PREPAID: {}</span>', formatted_balance)
        return format_html('<span style="color: #15803d; font-weight: bold;">CLEARED</span>')

    get_fee_status.short_description = "Accounting"

    def print_official_transcript(self, obj):
        if obj.fee_balance <= 0:
            url = reverse('official_leaving_transcript', args=[obj.id_number])
            return format_html(
                '<a href="{}" target="_blank" style="background: #001f3f; color: white; padding: 5px 10px; text-decoration: none; font-weight: bold; font-size: 10px; border-radius: 2px;">'
                'PRINT OFFICIAL</a>', url)
        return format_html('<small style="color: #94a3b8; font-style: italic;">HOLD: UNCLEARED</small>')

    print_official_transcript.short_description = "Registrar Print"

    def save_model(self, request, obj, form, change):
        obj.is_staff = False  # Ensure student status
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=False, is_superuser=False)


@admin.register(StaffUser)
class StaffUserAdmin(admin.ModelAdmin):
    form = StaffUserForm
    list_display = ('full_name', 'school', 'phone_number', 'id_number', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('full_name', 'phone_number', 'id_number')

    fieldsets = (
        ('Staff Identity', {
            'fields': ('full_name', 'id_number', 'phone_number', 'gender', 'profile_photo')
        }),
        ('Professional Assignment', {
            'fields': ('school', 'course'),
            'description': 'Select all schools/departments where this lecturer operates.'
        }),
        ('Account Access', {
            'fields': ('is_active', 'is_staff'),
        }),
    )

    def save_model(self, request, obj, form, change):
        obj.is_staff = True  # Force staff status
        if not change:
            obj.set_password(obj.id_number)  # Default password is ID
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=True, is_superuser=False)


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject_name', 'unit_code', 'marks', 'grade', 'is_published')
    list_filter = ('semester', 'grade', 'is_published', 'student__school')
    list_editable = ('is_published', 'marks')
    search_fields = ('student__full_name', 'unit_code', 'subject_name')
    actions = [print_academic_report]


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('reference_code', 'student', 'amount', 'method', 'date_paid')
    search_fields = ('reference_code', 'student__full_name', 'student__admission_number')
    list_filter = ('method', 'date_paid')

    def save_model(self, request, obj, form, change):
        student = obj.student
        remaining = student.fee_balance
        if obj.amount > remaining:
            messages.error(request,
                           f"REJECTED: Entry of KES {obj.amount} exceeds the student's total remaining balance of KES {remaining}.")
            return
        super().save_model(request, obj, form, change)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'audience', 'is_priority', 'date_posted')
    list_filter = ('audience', 'is_priority')
    list_editable = ('is_priority', 'audience')