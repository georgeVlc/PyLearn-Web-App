from django.shortcuts import render
from lessons.models import Lesson

def view_lessons(request):
    lessons = Lesson.objects.all()  # list lessons
    return render(request, 'lessons/view_lessons.html', {'lessons': lessons})
