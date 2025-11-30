from django.urls import path
from . import views

app_name = "scheduler"

urlpatterns = [
    # Home Dashboard Page
    path("", views.home, name="home"),

    # Teacher personal timetable
    path("my-timetable/", views.my_timetable, name="my_timetable"),

    # Timetable List & Detail Views
    path("timetables/", views.timetable_list, name="timetable_list"),
    path("class/<int:class_id>/", views.timetable_detail, name="timetable_detail"),
    path("class/<int:class_id>/pdf/", views.timetable_pdf, name="timetable_pdf"),
]
