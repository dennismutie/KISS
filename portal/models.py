import random
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models import Sum


class StudentManager(BaseUserManager):
    def create_user(self, phone_number, full_name, id_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("Users must have a phone number")
        if not password:
            password = id_number
        user = self.model(phone_number=phone_number, full_name=full_name, id_number=id_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, full_name, id_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone_number, full_name, id_number, password, **extra_fields)


class Student(AbstractBaseUser, PermissionsMixin):
    SCHOOL_CHOICES = [
        ('SCD', 'School of Community Dev. & Social Work'),
        ('SBS', 'School of Business Studies'),
        ('SHT', 'School of Hospitality & Tourism'),
        ('SBF', 'School of Beauty & Fashion'),
        ('SEE', 'School of Electrical Engineering'),
        ('SCI', 'School of Computing & IT'),
        ('SHS', 'School of Health Sciences'),
    ]
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female')]
    SEMESTER_CHOICES = [
        ('Sem 1', 'Semester 1'), ('Sem 2', 'Semester 2'), ('Sem 3', 'Semester 3'),
        ('Sem 4', 'Semester 4'), ('Sem 5', 'Semester 5'), ('Sem 6', 'Semester 6')
    ]
    OFFICIAL_TRANSCRIPT_CHOICES = [
        ('DRAFT', 'Ongoing / Draft'),
        ('PENDING', 'Request Pending'),
        ('ISSUED', 'Officially Issued'),
    ]

    # --- Basic Info ---
    phone_number = models.CharField(max_length=15, unique=True)
    full_name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=20, unique=True)
    admission_number = models.CharField(max_length=30, unique=True, null=True, blank=True)

    # INCREASED LENGTH: To support multiple selections for Staff/Lecturers
    school = models.CharField(max_length=500, null=True, blank=True)
    course = models.CharField(max_length=500, null=True, blank=True)

    profile_photo = models.ImageField(upload_to='students/', default='students/lec.png', null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES, default='Sem 1')

    # --- FINANCIAL ARCHITECTURE (DYNAMIC) ---
    total_semesters = models.PositiveIntegerField(default=1)
    fees_per_semester = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # --- GRADUATION & PROGRESS ---
    start_date = models.DateField(null=True, blank=True)
    duration_months = models.PositiveIntegerField(default=3)
    expected_graduation_date = models.DateField(null=True, blank=True)
    official_transcript_status = models.CharField(max_length=20, choices=OFFICIAL_TRANSCRIPT_CHOICES, default='DRAFT')
    session_reported = models.BooleanField(default=False)
    session_start_date = models.DateField(null=True, blank=True)
    session_end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = StudentManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name', 'id_number']

    @property
    def total_course_fees(self):
        """Calculates total cost based on Admin input: Sems x Fees"""
        return self.total_semesters * self.fees_per_semester

    @property
    def total_paid_sum(self):
        """Calculates actual receipts from FeePayment table"""
        return self.payments.aggregate(total=Sum('amount'))['total'] or 0

    @property
    def fee_balance(self):
        """
        DYNAMIC BALANCE: Total Fees - Total Paid.
        Positive = Owed | Negative = Prepaid
        """
        return self.total_course_fees - self.total_paid_sum

    def __str__(self):
        return f"{self.full_name} ({self.admission_number or self.id_number})"

    def save(self, *args, **kwargs):
        if not self.pk or not self.password:
            self.set_password(self.id_number)
        if self.password and not self.password.startswith(('pbkdf2_sha256$', 'bcrypt$', 'argon2')):
            self.set_password(self.password)
        if not self.admission_number and not self.is_staff:
            year = 2026
            rand_id = random.randint(1000, 9999)
            self.admission_number = f"KISS/{year}/{rand_id}"
        super().save(*args, **kwargs)


class FeePayment(models.Model):
    PAYMENT_METHODS = [('MPESA', 'M-Pesa'), ('CASH', 'Bank/Cash')]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_paid = models.DateField()
    method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='MPESA')
    reference_code = models.CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            student = self.student
            remaining_to_clearance = student.total_course_fees - student.total_paid_sum

            if self.amount > remaining_to_clearance:
                raise ValueError(
                    f"Overpayment Alert! Student only needs KES {remaining_to_clearance} "
                    f"to fully clear. You tried KES {self.amount}."
                )

        super().save(*args, **kwargs)


class ExamResult(models.Model):
    SEMESTER_CHOICES = [
        ('Sem 1', 'Semester 1'), ('Sem 2', 'Semester 2'), ('Sem 3', 'Semester 3'),
        ('Sem 4', 'Semester 4'), ('Sem 5', 'Semester 5'), ('Sem 6', 'Semester 6')
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_results')
    subject_name = models.CharField(max_length=100)
    unit_code = models.CharField(max_length=20)
    marks = models.PositiveIntegerField()
    grade = models.CharField(max_length=2, blank=True)
    classification = models.CharField(max_length=20, blank=True)
    semester = models.CharField(max_length=50, choices=SEMESTER_CHOICES, default="Sem 1")
    year = models.IntegerField(default=2026)
    is_published = models.BooleanField(default=True)
    entered_by = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, limit_choices_to={'is_staff': True},
                                   related_name='marks_entered')
    date_entered = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.marks >= 80:
            self.grade, self.classification = 'A', 'DISTINCTION'
        elif self.marks >= 65:
            self.grade, self.classification = 'B', 'CREDIT'
        elif self.marks >= 50:
            self.grade, self.classification = 'C', 'PASS'
        elif self.marks >= 40:
            self.grade, self.classification = 'D', 'SUPP'
        else:
            self.grade, self.classification = 'E', 'FAIL'
        super().save(*args, **kwargs)


class Announcement(models.Model):
    AUDIENCE_CHOICES = [('ALL', 'Everyone'), ('STUDENTS', 'Students Only'), ('STAFF', 'Staff Only')]
    title = models.CharField(max_length=200)
    content = models.TextField()
    audience = models.CharField(max_length=15, choices=AUDIENCE_CHOICES, default='ALL')
    author = models.ForeignKey(Student, on_delete=models.SET_NULL, related_name='announcements_posted', null=True)
    is_priority = models.BooleanField(default=False)
    date_posted = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"[{self.audience}] {self.title}"

    class Meta:
        db_table = 'portal_announcement'