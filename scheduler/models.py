from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

# -------------------------------------------------
# ROLE SYSTEM (used in navbar as user.profile.role)
# -------------------------------------------------
ROLE_CHOICES = (
    ('ADMIN', 'Admin'),
    ('TEACHER', 'Teacher'),
    ('STUDENT', 'Student'),
)


class UserProfile(models.Model):
    """
    One profile per User, with role: ADMIN / TEACHER / STUDENT.
    Accessed as user.profile in templates.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='STUDENT'
    )

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


# -------------------------------------------------
# TIMETABLE MODELS
# -------------------------------------------------

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=20, unique=True)
    max_periods_per_day = models.PositiveIntegerField(
        default=6,
        validators=[MinValueValidator(1)]
    )

    class Meta:
        ordering = ["code"]

    def __str__(self):
        full_name = self.user.get_full_name() or self.user.username
        return f"{full_name} ({self.code})"


class Room(models.Model):
    name = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField(default=30)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} (cap {self.capacity})"


class SchoolClass(models.Model):
    # Represents a grade-section combination e.g., 10-A
    name = models.CharField(max_length=50)
    strength = models.PositiveIntegerField(default=30)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    default_periods_per_week = models.PositiveIntegerField(default=5)

    # Optional hex color for fancy UI pills
    color_code = models.CharField(
        max_length=7,
        blank=True,
        default='',
        help_text="Optional hex color for this subject, e.g. #81E6D9"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TeacherSubject(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('teacher', 'subject')

    def __str__(self):
        return f"{self.teacher} - {self.subject}"


class Period(models.Model):
    # e.g. Mon 09:00-09:40 -> we'll represent day and order
    DAY_CHOICES = [
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
    ]
    day = models.IntegerField(choices=DAY_CHOICES)
    order = models.PositiveIntegerField()  # 1..n
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ('day', 'order')
        ordering = ['day', 'order']

    def __str__(self):
        return f"{self.get_day_display()} P{self.order}"


class Constraint(models.Model):
    """
    Period ko block karne ke liye:
    - teacher == null ho to "global block" (kisi ke liye available nahi)
    - teacher set ho to sirf us teacher ke liye block
    """
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True, blank=True)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    blocked = models.BooleanField(default=True)
    note = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Constraint {self.teacher or 'ANY'} {self.period}"


class TimetableEntry(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('school_class', 'period')
        ordering = ["school_class__name", "period__day", "period__order"]

    def __str__(self):
        return f"{self.school_class} | {self.period} | {self.subject}"

    def clean(self):
        """
        Smart validation:

        1) Teacher–Subject mapping hona chahiye (TeacherSubject).
        2) Same teacher ek hi period me 2 alag class me nahi jaa sakta.
        3) Same room ek hi period me 2 alag class ko nahi mil sakta.
        4) Constraint table respect karega (global & teacher-specific).
        5) Teacher ka max_periods_per_day cross na ho ek din me.
        """
        super().clean()
        errors = {}

        # 1) TeacherSubject mapping check
        if self.teacher_id and self.subject_id:
            from .models import TeacherSubject  # local import not needed actually but safe
            if not TeacherSubject.objects.filter(
                teacher=self.teacher,
                subject=self.subject
            ).exists():
                errors.setdefault("teacher", []).append(
                    f"{self.teacher} is not assigned to teach {self.subject}."
                )

        # 2) Teacher double booking (same day+period across classes)
        if self.teacher_id and self.period_id:
            clash_qs = TimetableEntry.objects.filter(
                teacher=self.teacher,
                period=self.period,
            ).exclude(pk=self.pk)
            if clash_qs.exists():
                errors.setdefault("teacher", []).append(
                    "This teacher is already assigned to another class in this period."
                )

        # 3) Room double booking
        if self.room_id and self.period_id:
            room_qs = TimetableEntry.objects.filter(
                room=self.room,
                period=self.period,
            ).exclude(pk=self.pk)
            if room_qs.exists():
                errors.setdefault("room", []).append(
                    "This room is already assigned to another class in this period."
                )

        # 4) Constraints (global or teacher-specific block)
        if self.period_id:
            constraint_qs = Constraint.objects.filter(
                period=self.period,
                blocked=True,
            )
            from django.db.models import Q
            if self.teacher_id:
                constraint_qs = constraint_qs.filter(
                    Q(teacher__isnull=True) | Q(teacher=self.teacher)
                )
            else:
                constraint_qs = constraint_qs.filter(teacher__isnull=True)

            if constraint_qs.exists():
                errors.setdefault("period", []).append(
                    "This period is blocked by a timetable constraint."
                )

        # 5) Teacher max_periods_per_day limit
        if self.teacher_id and self.period_id:
            same_day_count = TimetableEntry.objects.filter(
                teacher=self.teacher,
                period__day=self.period.day,
            ).exclude(pk=self.pk).count()

            if same_day_count + 1 > self.teacher.max_periods_per_day:
                errors.setdefault("teacher", []).append(
                    f"This will exceed {self.teacher}'s max periods per day "
                    f"({self.teacher.max_periods_per_day})."
                )

        if errors:
            raise ValidationError(errors)
