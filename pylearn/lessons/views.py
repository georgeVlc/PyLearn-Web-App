from django.shortcuts import render, get_object_or_404
from lessons.models import Lesson, Quiz

def view_lessons(request):
    lessons = Lesson.objects.all()  # list lessons
    return render(request, 'view_lessons.html', {'lessons': lessons})

def view_lesson_test(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)    # get specified lesson
    quizzes = lesson.quizzes.all()  # get all quizzes associated with that lesson
    return render(request, 'view_lesson_test.html', {'lesson': lesson, 'quizzes': quizzes}) # display lesson test