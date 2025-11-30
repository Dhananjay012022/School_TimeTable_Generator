from django.core.management.base import BaseCommand
from scheduler.models import SchoolClass, Subject, TeacherSubject, Period, Teacher, Room, TimetableEntry, Constraint
from django.db import transaction
import random

class Command(BaseCommand):
    help = 'Generate timetable for all classes'

    def handle(self, *args, **options):
        self.stdout.write("Starting timetable generation...")
        classes = list(SchoolClass.objects.all())
        periods = list(Period.objects.all().order_by('day','order'))
        rooms = list(Room.objects.all())
        if not classes or not periods or not rooms:
            self.stdout.write(self.style.ERROR("Please create classes, periods, teachers, subjects and rooms first."))
            return

        # Simple data structure: for each class we need a subject-to-remaining-count dict
        # For demonstration we assign each subject its default_periods_per_week
        class_subjects = {}
        for c in classes:
            # In practice you might have subject assignments per class, here pick all subjects
            sub_list = {}
            for s in Subject.objects.all():
                sub_list[s.id] = s.default_periods_per_week
            class_subjects[c.id] = sub_list

        # Clear existing timetable
        TimetableEntry.objects.all().delete()
        failed = []

        # For each class, try to fill every period
        for c in classes:
            success = self.fill_for_class(c, periods, class_subjects[c.id], rooms)
            if not success:
                failed.append(c.name)

        if failed:
            self.stdout.write(self.style.WARNING("Could not fully schedule: " + ", ".join(failed)))
        else:
            self.stdout.write(self.style.SUCCESS("Timetable generation completed."))

    def find_teacher_for_subject(self, subject_id):
        ts = TeacherSubject.objects.filter(subject_id=subject_id).select_related('teacher')
        if not ts.exists():
            return None
        return random.choice(list(ts)).teacher

    def is_teacher_available(self, teacher, period):
        # check Constraint
        if Constraint.objects.filter(teacher=teacher, period=period, blocked=True).exists():
            return False
        # check current assignments for teacher at this period
        return not TimetableEntry.objects.filter(teacher=teacher, period=period).exists()

    @transaction.atomic
    def fill_for_class(self, school_class, periods, subject_remaining, rooms):
        """
        Greedy fill: iterate periods. For each, pick a subject that still needs periods,
        find an available teacher for that subject, and a room with sufficient capacity.
        If stuck: attempt simple backtracking (retry last N assignments). This is simplified.
        """
        assignments = []  # (period, subject_id, teacher, room)
        for period in periods:
            # pick candidates sorted by how many left (largest first to avoid starvation)
            candidates = [ (sid, cnt) for sid,cnt in subject_remaining.items() if cnt>0 ]
            if not candidates:
                # no remaining subject -> put free or elective placeholder (skip)
                continue
            candidates.sort(key=lambda x: -x[1])
            placed = False
            # try candidates
            for sid, _ in candidates:
                teacher = self.find_teacher_for_subject(sid)
                if not teacher:
                    continue
                if not self.is_teacher_available(teacher, period):
                    continue
                # find room
                room = None
                for r in rooms:
                    if r.capacity >= school_class.strength and not TimetableEntry.objects.filter(room=r, period=period).exists():
                        room = r
                        break
                if not room:
                    continue
                # create entry
                subject = Subject.objects.get(pk=sid)
                TimetableEntry.objects.create(
                    school_class=school_class,
                    period=period,
                    subject=subject,
                    teacher=teacher,
                    room=room
                )
                subject_remaining[sid] -= 1
                assignments.append((period, sid, teacher.id, room.id))
                placed = True
                break
            if not placed:
                # Try simple backtracking: remove previous assignment and try alternative
                if assignments:
                    last_period, last_sid, last_teacher_id, last_room_id = assignments.pop()
                    # revert last assignment
                    TimetableEntry.objects.filter(school_class=school_class, period=last_period).delete()
                    subject_remaining[last_sid] += 1
                    # push current period to end and reattempt — naive but may help
                    periods.append(period)
                    continue
                else:
                    # cannot place at all and nothing to backtrack
                    return False
        return True
