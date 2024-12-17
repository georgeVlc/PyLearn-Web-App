from django.shortcuts import render, get_object_or_404, redirect
from lessons.models import Lesson, Quiz
from users.models import UserProgress, QuizAttempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required
def view_lessons(request, lesson_id=None):
    lessons = Lesson.objects.order_by('order')  # All lessons ordered
    current_lesson = None

    if lesson_id is not None:
        current_lesson = get_object_or_404(Lesson, id=lesson_id)
    else:
        current_lesson = lessons.first()  # Default to the first lesson if none is selected
    # Get the next lesson
    next_lesson = lessons.filter(order__gt=current_lesson.order).order_by('order').first()

    context = {
        'lessons': lessons,
        'current_lesson': current_lesson,
        'next_lesson': next_lesson,
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

    if request.method == 'POST':
        user_progress, created = UserProgress.objects.get_or_create(user=request.user)
        mistakes = []
        correct_count = 0  # Track correct answers

        for quiz in quizzes:
            user_answer_key = request.POST.get(f'quiz_{quiz.id}')  # Key chosen by user
            correct_answer_key = quiz.correct_answer  # Key for the correct answer
            passed = user_answer_key == correct_answer_key

            # Check if the attempt already exists
            existing_attempt = QuizAttempt.objects.filter(user_progress=user_progress, quiz=quiz).first()
            if existing_attempt:
                existing_attempt.score = 1 if passed else 0
                existing_attempt.passed = passed
                existing_attempt.attempts += 1  # Increment attempts
                existing_attempt.save()
            else:
                QuizAttempt.objects.create(
                    user_progress=user_progress,
                    quiz=quiz,
                    score=1 if passed else 0,
                    passed=passed
                )

            # Track mistakes with full answers
            if passed:
                correct_count += 1
            else:
                mistakes.append({
                    'question': quiz.question,
                    'user_answer': {'option': user_answer_key, 'answer': quiz.answer_choices.get(user_answer_key, "No answer selected")},
                    'correct_answer': { 'option': correct_answer_key, 'answer': quiz.answer_choices.get(correct_answer_key)} 
                })

        # Calculate the user's score percentage
        total_quizzes = len(quizzes)
        score_percentage = (correct_count / total_quizzes) * 100

        # Mark lesson as completed if the majority
        if correct_count >= total_quizzes // 2:
            user_progress.completed_lessons.add(lesson)

        # Pass the results to the template
        context = {
            'lesson': lesson,
            'score_percentage': score_percentage,
            'mistakes': mistakes,
            'total_quizzes': total_quizzes,
            'correct_count': correct_count
        }
        return render(request, 'view_test_results.html', context)

    # If not POST, render the test page
    return render(request, 'take_lesson_test.html', {'lesson': lesson, 'quizzes': quizzes})
