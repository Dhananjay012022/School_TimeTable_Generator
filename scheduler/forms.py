from django import forms
from .models import SchoolClass, Subject, Teacher, Room

class ClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ['name', 'strength']

# Add other forms as needed for admin UI (subject, teacher) — simple ModelForms
