import random
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


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
    SEMESTER_CHOICES = [('Sem 1', 'Semester 1'), ('Sem 2', 'Semester 2'), ('Sem 3', 'Semester 3')]

    phone_number = models.CharField(max_length=15, unique=True)
    full_name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=20, unique=True)
    admission_number = models.CharField(max_length=30, unique=True, null=True, blank=True)
    fee_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    school = models.CharField(max_length=100, choices=SCHOOL_CHOICES, null=True, blank=True)
    course = models.CharField(max_length=100, null=True, blank=True)
    profile_photo = models.ImageField(upload_to='students/', default='students/lec.png', null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES, default='Sem 1')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = StudentManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name', 'id_number']

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
            student.fee_balance -= self.amount
            student.save()
        super().save(*args, **kwargs)


class ExamResult(models.Model):
    SEMESTER_CHOICES = [('Sem 1', 'Semester 1'), ('Sem 2', 'Semester 2'), ('Sem 3', 'Semester 3')]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_results')
    subject_name = models.CharField(max_length=100)
    unit_code = models.CharField(max_length=20)
    marks = models.PositiveIntegerField()
    grade = models.CharField(max_length=2, blank=True)
    classification = models.CharField(max_length=20, blank=True)
    semester = models.CharField(max_length=50, choices=SEMESTER_CHOICES, default="Sem 1")
    year = models.IntegerField(default=2026)

    # UPDATED: Changed default to True for instant results
    is_published = models.BooleanField(default=True)

    entered_by = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, limit_choices_to={'is_staff': True},
                                   related_name='marks_entered')
    date_entered = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Professional Kenyan Grading Scale
        if self.marks >= 80:
            self.grade = 'A'
            self.classification = 'DISTINCTION'
        elif self.marks >= 65:
            self.grade = 'B'
            self.classification = 'CREDIT'
        elif self.marks >= 50:
            self.grade = 'C'
            self.classification = 'PASS'
        elif self.marks >= 40:
            self.grade = 'D'
            self.classification = 'SUPP'
        else:
            self.grade = 'E'
            self.classification = 'FAIL'
        super().save(*args, **kwargs)


class Announcement(models.Model):
    AUDIENCE_CHOICES = [('ALL', 'Everyone'), ('STUDENTS', 'Students Only'), ('STAFF', 'Staff Only')]
    title = models.CharField(max_length=200)
    content = models.TextField()
    audience = models.CharField(max_length=15, choices=AUDIENCE_CHOICES, default='ALL')
    author = models.ForeignKey(Student, on_delete=models.SET_NULL, related_name='announcements_posted', null=True)
    is_priority = models.BooleanField(default=False)
    date_posted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.audience}] {self.title}"

    class Meta:
        db_table = 'portal_announcement'