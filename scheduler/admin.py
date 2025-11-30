from django.contrib import admin
from django import forms

from .models import (
    UserProfile,
    Teacher,
    Room,
    SchoolClass,
    Subject,
    TeacherSubject,
    Period,
    Constraint,
    TimetableEntry,
)

# ==========================
# CUSTOM FORMS
# ==========================

class SubjectAdminForm(forms.ModelForm):
    """
    Subject ke colour ke liye color picker widget.
    """
    class Meta:
        model = Subject
        fields = "__all__"
        widgets = {
            "color_code": forms.TextInput(attrs={"type": "color"}),
        }


# ==========================
# INLINES
# ==========================

class TimetableEntryInline(admin.TabularInline):
    """
    Timetable entries ko SchoolClass / Teacher / Period ke andar inline dikhaane ke liye.
    """
    model = TimetableEntry
    extra = 0
    autocomplete_fields = ["subject", "teacher", "room", "period"]
    readonly_fields = ("created_at",)


class ConstraintInline(admin.TabularInline):
    """
    Period ke saath directly constraints manage karne ke liye.
    """
    model = Constraint
    extra = 0
    autocomplete_fields = ["teacher"]


# ==========================
# USER PROFILE ADMIN
# ==========================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")


# ==========================
# CORE MASTER DATA
# ==========================

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("code", "get_name", "max_periods_per_day")
    search_fields = (
        "code",
        "user__username",
        "user__first_name",
        "user__last_name",
    )
    inlines = [TimetableEntryInline]

    def get_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_name.short_description = "Name"


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity")
    search_fields = ("name",)
    list_filter = ("capacity",)


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ("name", "strength")
    search_fields = ("name",)
    inlines = [TimetableEntryInline]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    form = SubjectAdminForm
    list_display = ("name", "code", "color_code", "default_periods_per_week")
    search_fields = ("name", "code")


@admin.register(TeacherSubject)
class TeacherSubjectAdmin(admin.ModelAdmin):
    list_display = ("teacher", "subject")
    list_filter = ("teacher", "subject")
    search_fields = (
        "teacher__code",
        "teacher__user__first_name",
        "teacher__user__last_name",
        "subject__name",
        "subject__code",
    )
    autocomplete_fields = ["teacher", "subject"]


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ("day", "order", "start_time", "end_time")
    list_filter = ("day",)
    ordering = ("day", "order")
    inlines = [ConstraintInline, TimetableEntryInline]

    # 👇 ye line add ki hai error fix ke liye
    search_fields = (
        "order",
        "start_time",
        "end_time",
    )


@admin.register(Constraint)
class ConstraintAdmin(admin.ModelAdmin):
    list_display = ("period", "teacher", "blocked", "note")
    list_filter = ("blocked", "teacher", "period__day")
    search_fields = (
        "note",
        "teacher__code",
        "teacher__user__first_name",
        "teacher__user__last_name",
        "period__order",
    )
    autocomplete_fields = ["teacher", "period"]


# ==========================
# TIMETABLE ENTRY ADMIN
# ==========================

@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = (
        "school_class",
        "period",
        "subject",
        "teacher",
        "room",
        "created_at",
    )
    list_filter = (
        "school_class",
        "period__day",
        "teacher",
        "room",
    )
    search_fields = (
        "school_class__name",
        "subject__name",
        "subject__code",
        "teacher__code",
        "teacher__user__first_name",
        "teacher__user__last_name",
        "room__name",
        "period__order",
    )
    autocomplete_fields = ["school_class", "period", "subject", "teacher", "room"]
    readonly_fields = ("created_at",)
