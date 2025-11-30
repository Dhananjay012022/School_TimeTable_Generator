# timetable_project/scheduler/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from .models import (
    TimetableEntry,
    SchoolClass,
    Period,
    Teacher,
)


# -----------------------------
# DASHBOARD (HOME)
# -----------------------------
@login_required
def home(request):
    total_classes = SchoolClass.objects.count()
    total_teachers = Teacher.objects.count()
    total_timetables = (
        TimetableEntry.objects.values("school_class").distinct().count()
    )

    recent = (
        TimetableEntry.objects
        .select_related("school_class", "subject", "period")
        .order_by("-created_at")[:6]
    )

    return render(request, "scheduler/dashboard.html", {
        "total_classes": total_classes,
        "total_teachers": total_teachers,
        "total_timetables": total_timetables,
        "recent_timetables": recent,
    })


# -----------------------------
# TIMETABLE LIST
# -----------------------------
@login_required
def timetable_list(request):
    classes = SchoolClass.objects.all().order_by("name")
    return render(request, "scheduler/timetable_list.html", {
        "classes": classes,
    })


# -----------------------------
# CLASS TIMETABLE DETAIL (HTML)
# -----------------------------
def _build_timetable_context_for_class(school_class):
    """
    Helper: class timetable ka shared context banata hai
    (detail view + printable view dono use kar sakte hain).
    """
    periods = Period.objects.all().order_by("day", "order")

    if not periods.exists():
        return {
            "school_class": school_class,
            "period_orders": [],
            "rows": [],
            "periods": periods,
        }

    period_orders = sorted({p.order for p in periods})
    days = sorted({p.day for p in periods})
    day_label_map = {code: label for code, label in periods.model.DAY_CHOICES}

    entries = (
        TimetableEntry.objects
        .filter(school_class=school_class)
        .select_related("period", "subject", "teacher__user", "room")
    )

    entries_map = {(e.period.day, e.period.order): e for e in entries}

    rows = []
    for day in days:
        cells = [entries_map.get((day, order)) for order in period_orders]
        rows.append({
            "day": day,
            "label": day_label_map.get(day, f"Day {day}"),
            "cells": cells,
        })

    return {
        "school_class": school_class,
        "periods": periods,
        "period_orders": period_orders,
        "rows": rows,
    }


@login_required
def timetable_detail(request, class_id):
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    context = _build_timetable_context_for_class(school_class)
    return render(request, "scheduler/timetable_detail.html", context)


# -----------------------------
# TEACHER "MY TIMETABLE"
# -----------------------------
@login_required
def my_timetable(request):
    """
    Logged-in TEACHER ke liye personal timetable.
    user.profile.role == 'TEACHER' nahi hua to dashboard pe redirect.
    """
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != "TEACHER":
        return redirect("scheduler:home")

    teacher = get_object_or_404(Teacher, user=request.user)

    periods = Period.objects.all().order_by("day", "order")
    if not periods.exists():
        return render(request, "scheduler/teacher_timetable.html", {
            "teacher": teacher,
            "period_orders": [],
            "rows": [],
            "periods": periods,
        })

    period_orders = sorted({p.order for p in periods})
    days = sorted({p.day for p in periods})
    day_label_map = {code: label for code, label in periods.model.DAY_CHOICES}

    entries = (
        TimetableEntry.objects
        .filter(teacher=teacher)
        .select_related("period", "subject", "school_class", "room")
    )

    entries_map = {(e.period.day, e.period.order): e for e in entries}

    rows = []
    for day in days:
        cells = [entries_map.get((day, order)) for order in period_orders]
        rows.append({
            "day": day,
            "label": day_label_map.get(day, f"Day {day}"),
            "cells": cells,
        })

    return render(request, "scheduler/teacher_timetable.html", {
        "teacher": teacher,
        "periods": periods,
        "period_orders": period_orders,
        "rows": rows,
    })


# -----------------------------
# "PDF" EXPORT VIEW (PRINTABLE HTML)
# -----------------------------
@login_required
def timetable_pdf(request, class_id):
    """
    FAST + RELIABLE VERSION:
    - Ab WeasyPrint use nahi kar rahe
    - Sirf print-friendly HTML return karte hain
    - Browser se Ctrl+P → Save as PDF
    """
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    context = _build_timetable_context_for_class(school_class)

    # Tu already ye template use kar raha hai, agar nahi hai
    # to timetable_detail.html ka ek copy bana ke
    # "scheduler/printable_timetable.html" naam se rakh sakta hai.
    return render(request, "scheduler/printable_timetable.html", context)
