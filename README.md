# 🏫 School TimeTable Generator

A modern **School Timetable Management** project built with **Python, Django, HTML, CSS, JS & Bootstrap**.

- ✔️ Clean, responsive dashboard UI  
- ✔️ Clash detection (teacher / room double booking)  
- ✔️ Role-ready structure (Admin, Teacher, Student via `UserProfile`)  
- ✔️ Teacher–Subject mapping & constraints  
- ✔️ Printable / PDF-friendly timetable view  
- ✔️ Smart Django Admin configuration  

---

## 🚀 Features

### 🧱 Core Models

- **SchoolClass** – Class / Section (e.g. `10-A`, `B.Tech CSE 3rd Year`)
- **Teacher** – Linked with Django `User`, has `code` & `max_periods_per_day`
- **Subject** – Name, code & optional `color_code` for UI pills
- **Room** – Name & capacity
- **Period** – Day + order + optional time (`start_time`, `end_time`)
- **TimetableEntry** – One cell in the timetable grid  
  (`SchoolClass + Period + Subject + Teacher + Room`)

### ⚔️ Clash Detection & Constraints

Implemented in `TimetableEntry.clean()`:

- ❌ Same **teacher** cannot be in two classes in the **same period**
- ❌ Same **room** cannot be used by two classes in the **same period**
- ❌ Blocked periods (via **Constraint** model) are not allowed
- ❌ Teacher cannot exceed `max_periods_per_day`
- ❌ Teacher must be mapped to subject via **TeacherSubject** relation

All this validation is enforced when saving from Django Admin or forms.

### 📊 Dashboard

- Total **classes**, **teachers**, and **active timetables**
- Recent timetable activity table
- Modern glass-style layout with icons & cards

### 📅 Timetable Views

- **Class Timetable Detail**
  - Grid by **Day × Period**
  - Colorful subject pills
  - Teacher & Room shown under each cell
  - Legend & notes section

- **Teacher Timetable**
  - Separate personalised timetable for logged-in teacher  
    (`user.profile.role == "TEACHER"`)

### 🖨 Printable / PDF-friendly Timetable

- Route: `/class/<id>/pdf/`
- Opens a **print-optimized landscape layout**
- Centered heading (`Timetable – CLASS`), coloured subject tags
- Use browser `Ctrl + P → Save as PDF` to generate a nicely formatted PDF

---

## 🛠 Tech Stack

- **Backend:** Django
- **Frontend:** HTML, CSS, Bootstrap, Remix Icons
- **Auth:** Django’s built-in `User` + `UserProfile` for roles
- **Database:** SQLite (can be swapped to PostgreSQL/MySQL)

---

## 📂 Project Structure (short)

```text
timetable_project/
├─ manage.py
├─ timetable_project/
│  ├─ settings.py
│  ├─ urls.py
│  └─ wsgi.py
├─ scheduler/
│  ├─ models.py          # Core timetable models + validation
│  ├─ views.py           # Dashboard, timetable views, printable view
│  ├─ urls.py
│  ├─ admin.py           # Advanced admin configuration
│  ├─ forms.py
│  └─ templatetags/
│     ├─ __init__.py
│     └─ scheduler_extras.py
└─ templates/scheduler/
   ├─ base.html
   ├─ dashboard.html
   ├─ timetable_list.html
   ├─ timetable_detail.html
   ├─ printable_timetable.html
   └─ teacher_timetable.html
