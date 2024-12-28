import os
import json
from .models import UserProgress, QuizAttempt, TaskAttempt
from lessons.models import Lesson, Quiz, Task
from django.db.utils import OperationalError
from django.db.models import Avg, Count, Sum, Q, F
from lessons.utils import get_chapter_number_for_lesson


def delete_all_progress_and_attempts():
    UserProgress.objects.all().delete()
    QuizAttempt.objects.all().delete()
    TaskAttempt.objects.all().delete()
    print("All user progress and attempts have been deleted from the database.")

def get_quiz_lessons(user_progress):
    return Lesson.objects.filter(
        quizzes__quizattempt__user_progress=user_progress,
        is_task_based=False
    ).annotate(
        total_attempts=Count('quizzes__quizattempt', distinct=True),
        total_quizzes=Count('quizzes', distinct=True)
    ).distinct()

def get_task_lessons(user_progress):
    return Lesson.objects.filter(
        tasks__taskattempt__user_progress=user_progress,
        is_task_based=True
    ).annotate(
        total_attempts=Count('tasks__taskattempt', distinct=True),
        total_tasks=Count('tasks', distinct=True)
    ).distinct()

def process_quiz_lessons(quiz_lessons, user_progress):
    total_points = 0
    for lesson in quiz_lessons:
        user_correct_answers = QuizAttempt.objects.filter(
            user_progress=user_progress,
            quiz__lesson=lesson
        ).aggregate(total_correct=Sum('passed'))['total_correct'] or 0

        total_quizzes = lesson.total_quizzes
        lesson.accuracy = calculate_accuracy(user_correct_answers, total_quizzes)
        lesson.correct_answers = user_correct_answers
        lesson.passed = lesson.accuracy >= 50
        lesson.chapter_id = get_chapter_number_for_lesson(lesson.id)

        lesson.points_earned = QuizAttempt.objects.filter(
            user_progress=user_progress,
            quiz__lesson=lesson,
            passed=True
        ).aggregate(total_points=Sum(F('quiz__points')))['total_points'] or 0
        total_points += lesson.points_earned

        lesson.points_available = QuizAttempt.objects.filter(
            user_progress=user_progress,
            quiz__lesson=lesson
        ).aggregate(total_points=Sum(F('quiz__points')))['total_points'] or 0

    return total_points

def process_task_lessons(task_lessons, user_progress):
    total_points = 0
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
        total_points += lesson.points_earned

        lesson.points_available = TaskAttempt.objects.filter(
            user_progress=user_progress,
            task__lesson=lesson
        ).aggregate(total_points=Sum(F('task__points')))['total_points'] or 0

    return total_points

def calculate_accuracy(correct, total):
    return round((correct / total) * 100, 2) if total > 0 else 0

def calculate_overall_stats(quiz_lessons, task_lessons):
    total_lessons = len(quiz_lessons) + len(task_lessons)
    passed_quiz_lessons = [lesson for lesson in quiz_lessons if lesson.passed]
    passed_task_lessons = [lesson for lesson in task_lessons if lesson.passed]
    all_passed_lessons = passed_quiz_lessons + passed_task_lessons

    overall_accuracy = sum([lesson.accuracy for lesson in list(quiz_lessons) + list(task_lessons)]) / total_lessons
    overall_accuracy = round(overall_accuracy, 2)

    return overall_accuracy, total_lessons, len(all_passed_lessons)

def get_progress_time_series(user_id):
    quiz_attempts = QuizAttempt.objects.filter(user_progress__user_id=user_id).order_by('created_at')
    task_attempts = TaskAttempt.objects.filter(user_progress__user_id=user_id).order_by('created_at')

    data = {
        'quiz_progress': [],
        'task_progress': []
    }

    for attempt in quiz_attempts:
        data['quiz_progress'].append({
            'timestamp': attempt.created_at,
            'points': attempt.points,
            'attempt_number': attempt.attempts,
            'quiz': attempt.quiz.question,
            'lesson': attempt.quiz.lesson.title
        })

    for attempt in task_attempts:
        data['task_progress'].append({
            'timestamp': attempt.created_at,
            'points': attempt.points,
            'accuracy': attempt.accuracy,
            'attempt_number': attempt.attempts,
            'task': attempt.task.description if len(attempt.task.description) < 30 else attempt.task.description[:30],
            'lesson': attempt.task.lesson.title
        })

    return data
