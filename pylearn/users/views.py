from django.shortcuts import render
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from .models import UserProgress, QuizAttempt, TaskAttempt
from lessons.models import chapter_size
from django.contrib.auth import authenticate, login,  logout
from django.contrib.auth import authenticate, login as auth_login 
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Avg, Count, Sum, Q, F
from django.contrib.auth.decorators import login_required
from lessons.models import Lesson, Quiz
from math import ceil
from lessons.utils import get_chapter_number_for_lesson
# Create your views here.

def view_users(request):
    users = User.objects.all()  # List users
    return render(request, 'view_users.html', {'users': users})

from django.db.models import Sum, F

@login_required
def view_user_attempts(request, user_id):
    user_progress = get_object_or_404(UserProgress, user_id=user_id)

    # Separate quiz-based and task-based lessons
    quiz_lessons = Lesson.objects.filter(
        quizzes__quizattempt__user_progress=user_progress,
        is_task_based=False
    ).annotate(
        total_attempts=Count('quizzes__quizattempt', distinct=True),
        total_quizzes=Count('quizzes', distinct=True)
    ).distinct()

    task_lessons = Lesson.objects.filter(
        tasks__taskattempt__user_progress=user_progress,
        is_task_based=True
    ).annotate(
        total_attempts=Count('tasks__taskattempt', distinct=True),
        total_tasks=Count('tasks', distinct=True)
    ).distinct()

    all_lessons = list(quiz_lessons) + list(task_lessons)
    total_points_earned = 0
    
    # Process quiz-based lessons
    for lesson in quiz_lessons:
        user_correct_answers = QuizAttempt.objects.filter(
            user_progress=user_progress,
            quiz__lesson=lesson
        ).aggregate(total_correct=Sum('passed'))['total_correct'] or 0

        total_quizzes = lesson.total_quizzes
        lesson.accuracy = (
            (user_correct_answers / total_quizzes) * 100
            if total_quizzes > 0
            else 0
        )
        lesson.accuracy = round(lesson.accuracy, 2)
        lesson.correct_answers = user_correct_answers
        lesson.passed = lesson.accuracy >= 50
        lesson.chapter_id = get_chapter_number_for_lesson(lesson.id)
        
        lesson.points_earned = QuizAttempt.objects.filter(
            user_progress=user_progress,
            quiz__lesson=lesson,
            passed=True
        ).aggregate(total_points=Sum(F('quiz__points')))['total_points'] or 0
        total_points_earned += lesson.points_earned
        
        lesson.points_available = QuizAttempt.objects.filter(
            user_progress=user_progress,
            quiz__lesson=lesson
        ).aggregate(total_points=Sum(F('quiz__points')))['total_points'] or 0

    # Process task-based lessons
    for lesson in task_lessons:
        user_attempts = TaskAttempt.objects.filter(
            user_progress=user_progress,
            task__lesson=lesson,
        )

        total_tasks = lesson.total_tasks            
        lesson.accuracy = sum([attempt.accuracy for attempt in user_attempts]) / total_tasks
        lesson.accuracy = round(lesson.accuracy, 2)
        lesson.passed = lesson.accuracy >= 50
        lesson.chapter_id = get_chapter_number_for_lesson(lesson.id)

        lesson.points_earned = TaskAttempt.objects.filter(
            user_progress=user_progress,
            task__lesson=lesson,
            passed=True
        ).aggregate(total_points=Sum(F('task__points')))['total_points'] or 0
        total_points_earned += lesson.points_earned
        
        lesson.points_available = TaskAttempt.objects.filter(
            user_progress=user_progress,
            task__lesson=lesson
        ).aggregate(total_points=Sum(F('task__points')))['total_points'] or 0
        print(f'{lesson.points_earned=}, {lesson.points_available}')
                
    # Calculate overall stats
    total_quizzes_attempted = QuizAttempt.objects.filter(user_progress=user_progress).count()
    total_correct_quizzes = QuizAttempt.objects.filter(user_progress=user_progress).aggregate(
        total_correct=Sum('passed')
    )['total_correct'] or 0

    total_tasks_attempted = TaskAttempt.objects.filter(user_progress=user_progress).count()
    total_passed_tasks = TaskAttempt.objects.filter(user_progress=user_progress, passed=True).count()
    total_lesson_attempts_count = len(quiz_lessons) + len(task_lessons)
    
    passed_quiz_lessons = [lesson for lesson in quiz_lessons if lesson.passed]
    passed_task_lessons = [lesson for lesson in task_lessons if lesson.passed]
    all_passed_lessons = passed_quiz_lessons + passed_task_lessons
    
    overall_accuracy = sum([lesson.accuracy for lesson in all_lessons]) / len(all_lessons)
    overall_accuracy = round(overall_accuracy, 2)

    # Prepare context
    context = {
        'user_progress': user_progress,
        'quiz_lessons': quiz_lessons,
        'task_lessons': task_lessons,
        'overall_accuracy': overall_accuracy,
        'total_attempts_count': total_lesson_attempts_count,
        'total_lessons_passed': len(all_passed_lessons),
        'total_points_earned': total_points_earned
    }

    return render(request, 'view_user_attempts.html', context)
    
def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
        else:
            user = User.objects.create_user(username=username, password=password)
            user.save()
            messages.success(request, 'Account created successfully!')
            return redirect('users:login')
    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            if not UserProgress.objects.filter(user=user).exists():
                UserProgress.objects.create(user=user)
            return redirect('home')  # Redirect to the home page
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

