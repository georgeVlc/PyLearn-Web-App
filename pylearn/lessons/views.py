from django.shortcuts import render, get_object_or_404, redirect
from lessons.models import Lesson, Quiz
from users.models import UserProgress, QuizAttempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

CHAPTER_SIZE = 10

@login_required
def view_chapters(request):
    lessons = Lesson.objects.order_by('order')  # Fetch all lessons
    chapters = {}

    # Group lessons into chapters
    current_chapter = []
    chapter_number = 1
    for idx, lesson in enumerate(lessons):
        current_chapter.append(lesson)

        # After 10 lessons, close the chapter and start a new one
        if (idx + 1) % CHAPTER_SIZE == 0 or idx == len(lessons) - 1:
            chapters[chapter_number] = current_chapter
            current_chapter = []
            chapter_number += 1

    context = {
        'chapters': chapters,
    }
    return render(request, 'view_chapters.html', context)

@login_required
def view_lessons(request, chapter_id=None, lesson_id=None):
    # Determine the lessons for the requested chapter
    if chapter_id == 1 and lesson_id >= CHAPTER_SIZE:
        chapter_id = lesson_id // CHAPTER_SIZE + 1

    start_order = (chapter_id - 1) * CHAPTER_SIZE
    end_order = chapter_id * CHAPTER_SIZE
    
    lessons = Lesson.objects.filter(order__gte=start_order, order__lt=end_order).order_by('order')
    current_lesson = None

    
    if lesson_id is not None:
        if lesson_id == 0:
            current_lesson = get_object_or_404(Lesson, id=(chapter_id-1)*CHAPTER_SIZE)
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
    
    if request.method == 'POST':
        user_progress, created = UserProgress.objects.get_or_create(user=request.user)
        mistakes = []
        correct_count = 0  # Track correct answers
        
        # Check if this is a new lesson attempt
        lesson_attempts = QuizAttempt.objects.filter(
            user_progress=user_progress, quiz__lesson=lesson
        ).values('user_progress').distinct().count()
        
        # Increment lesson attempts (only count when a test is taken)
        lesson_attempts += 1
        
        for quiz in quizzes:
            user_answer_key = request.POST.get(f'quiz_{quiz.id}')  # Key chosen by user
            correct_answer_key = quiz.correct_answer  # Key for the correct answer
            passed = user_answer_key == correct_answer_key

            # Update or create quiz attempts
            existing_attempt = QuizAttempt.objects.filter(user_progress=user_progress, quiz=quiz).first()
            if existing_attempt:
                existing_attempt.score = 1 if passed else 0
                existing_attempt.passed = passed
                existing_attempt.attempts = lesson_attempts  # Track by lesson attempt
                existing_attempt.save()
            else:
                QuizAttempt.objects.create(
                    user_progress=user_progress,
                    quiz=quiz,
                    score=1 if passed else 0,
                    passed=passed,
                    attempts=lesson_attempts
                )

            # Track mistakes with full answers
            if passed:
                correct_count += 1
            else:
                mistakes.append({
                    'question': quiz.question,
                    'user_answer': {
                        'option': user_answer_key,
                        'answer': quiz.answer_choices.get(user_answer_key, "No answer selected")
                    },
                    'correct_answer': {
                        'option': correct_answer_key,
                        'answer': quiz.answer_choices.get(correct_answer_key)
                    }
                })

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
            'lesson_attempts': lesson_attempts
        }
        return render(request, 'view_test_results.html', context)

    # If not POST, render the test page
    return render(request, 'take_lesson_test.html', {'lesson': lesson, 'quizzes': quizzes})
