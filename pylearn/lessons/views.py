from django.shortcuts import render, get_object_or_404, redirect
from lessons.models import Lesson, Quiz, chapter_size, chapter_titles, chapter_difficulties
from users.models import UserProgress, QuizAttempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .utils import *


@login_required
def view_chapters(request):
    lessons = Lesson.objects.order_by('order')  # Fetch all lessons
    chapters = {}

    # Group lessons into chapters
    current_chapter = {}
    chapter_number = 1
    for idx, lesson in enumerate(lessons):
        current_chapter.setdefault('lessons', []).append(lesson)

        # After 10 lessons, close the chapter and start a new one
        if (idx + 1) % chapter_size == 0 or idx == len(lessons) - 1:
            current_chapter['title'] = chapter_titles[chapter_number-1]
            current_chapter['difficulty'] = chapter_difficulties[chapter_number-1]
            current_chapter['number'] = chapter_number
            chapters[chapter_number] = current_chapter
            current_chapter = {}
            chapter_number += 1

    context = {
        'chapters': chapters,
    }
    return render(request, 'view_chapters.html', context)

@login_required
def view_lessons(request, chapter_id=None, lesson_id=None):
    # Determine the lessons for the requested chapter
    if chapter_id == 1 and lesson_id >= chapter_size:
        chapter_id = lesson_id // chapter_size + 1

    start_order = (chapter_id - 1) * chapter_size
    end_order = chapter_id * chapter_size
    
    lessons = Lesson.objects.filter(order__gte=start_order, order__lt=end_order).order_by('order')
    current_lesson = None

    
    if lesson_id is not None:
        if lesson_id == 0:
            current_lesson = get_object_or_404(Lesson, id=(chapter_id-1)*chapter_size)
        else:
            current_lesson = get_object_or_404(Lesson, id=lesson_id)
    else:
        current_lesson = lessons.first()  # Default to the first lesson in the chapter

    # Get the next lesson within the chapter
    next_lesson = lessons.filter(order__gt=current_lesson.order).order_by('order').first()

    context = {
        'lessons': lessons,
        'current_lesson': current_lesson,
        'next_lesson': next_lesson,
        'chapter_id': chapter_id,
    }
    return render(request, 'view_lessons.html', context)

@login_required
def view_lesson_test(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)    # get specified lesson
    quizzes = lesson.quizzes.all()  # get all quizzes associated with that lesson
    return render(request, 'view_lesson_test.html', {'lesson': lesson, 'quizzes': quizzes}) # display lesson test

@login_required
def take_lesson_test(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    quizzes = lesson.quizzes.all()
    tasks = lesson.tasks.all()
    # print(f'{lesson.title=}')
    
    if request.method == 'POST':
        user_progress, created = UserProgress.objects.get_or_create(user=request.user)
        if lesson.is_task_based:
            update_task_attempts(request)
            # correct_count, mistakes = track_test_results(request, quizzes)
        else:
            update_quiz_attempts(request, quizzes, user_progress, lesson)
            correct_count, mistakes = track_test_results(request, quizzes)
            
        
        # Calculate score percentage for the entire lesson
        total_quizzes = len(quizzes)
        score_percentage = (correct_count / total_quizzes) * 100

        # Mark lesson as completed if the majority of quizzes are correct
        if correct_count >= total_quizzes // 2:
            user_progress.completed_lessons.add(lesson)

        # Pass results to the template
        context = {
            'lesson': lesson,
            'score_percentage': score_percentage,
            'mistakes': mistakes,
            'total_quizzes': total_quizzes,
            'correct_count': correct_count,
        }
        
        if is_recap_lesson(lesson):
            recommendations = generate_recommendations(mistakes, Lesson.objects.all())
            print(f'{recommendations=}')
            context['recommendations'] = recommendations

        return render(request, 'view_test_results.html', context)

    # If not POST, render the test page
    return render(request, 'take_lesson_test.html', {'lesson': lesson, 'quizzes': quizzes, 'tasks': tasks})
