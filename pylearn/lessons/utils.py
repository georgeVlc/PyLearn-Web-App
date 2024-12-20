import os
import json
from .models import Lesson, Quiz
from users.models import UserProgress, QuizAttempt
from django.db.utils import OperationalError
from difflib import SequenceMatcher


def load_lessons_and_quizzes():
    lessons_path = "lessons/templates/lessons_html/"
    quizzes_path = "lessons/data/lessons_quizzes/"

    try:
        # Iterate through all lesson HTML files
        for lesson_file in os.listdir(lessons_path):
            if lesson_file.endswith(".html"):
                lesson_tokens = lesson_file.split(".") # Splitting the lesson file-name on '.'
                lesson_tokens = lesson_tokens[0].split("_") # Splitting on '_' and excluding the file extention
                lesson_id = int(lesson_tokens[0])  # Extract lesson ID from filename
                lesson_title = ' '.join([token.capitalize() for token in lesson_tokens[1:]])  # Capitalize each token
                print(f'{lesson_id=}, {lesson_title=}')
                
                with open(os.path.join(lessons_path, lesson_file), "r") as file:
                    content = file.read()

                # Create or update the lesson in the database
                lesson, created = Lesson.objects.update_or_create(
                    id=lesson_id,
                    defaults={
                        "title": lesson_title,
                        "content": content,
                        "order": lesson_id,
                    },
                )

                # Load quizzes for this lesson
                quiz_file_path = os.path.join(quizzes_path, f"{('_').join(lesson_tokens)}.json")
                if os.path.exists(quiz_file_path):
                    with open(quiz_file_path, "r") as file:
                        quiz_data = json.load(file)

                    for quiz in quiz_data:
                        Quiz.objects.update_or_create(
                            lesson=lesson,
                            question=quiz["question"],
                            defaults={
                                "answer_choices": quiz["answer_choices"],
                                "correct_answer": quiz["correct_answer"],
                            },
                        )
    except OperationalError:
        # Handle the case where the database is not ready (e.g., during migrations)
        print("Database not ready. Skipping lesson preloading.")
        # Path to lessons and quizzes data


def delete_all_lessons_and_quizzes():
    Quiz.objects.all().delete()
    Lesson.objects.all().delete()
    print("All lessons and quizzes have been deleted from the database.")

def update_quiz_attempts(request, quizzes, user_progress, lesson):
    lesson_attempts = QuizAttempt.objects.filter(
        user_progress=user_progress, quiz__lesson=lesson
    ).values('user_progress').distinct().count()
        
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

def track_test_results(request, quizzes):
    correct_count = 0
    mistakes = []
    
    for quiz in quizzes:
        user_answer_key = request.POST.get(f'quiz_{quiz.id}')  # Key chosen by user
        correct_answer_key = quiz.correct_answer  # Key for the correct answer
        passed = user_answer_key == correct_answer_key
        
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
    return correct_count, mistakes

def is_recap_lesson(lesson):
    return "recap" in lesson.title.lower()


def match_question_to_lessons(question, lessons):
    """
    Match a quiz question to the most relevant lessons.
    """
    best_match = None
    best_score = 0

    for lesson in lessons:
        similarity = SequenceMatcher(None, question.lower(), lesson.title.lower()).ratio()
        if similarity > best_score:
            best_score = similarity
            best_match = lesson

    return best_match, best_score

def generate_recommendations(mistakes, all_lessons):
    """
    Recommend lessons based on quiz mistakes.
    """
    lesson_recommendations = {}

    for mistake in mistakes:
        question = mistake['question']
        matched_lesson, similarity = match_question_to_lessons(question, all_lessons)
        
        if matched_lesson:
            if matched_lesson.id not in lesson_recommendations:
                lesson_recommendations[matched_lesson.id] = {
                    'lesson': matched_lesson,
                    'count': 0,
                    'similarity': similarity
                }
            lesson_recommendations[matched_lesson.id]['count'] += 1

    # Sort recommendations by mistake count and similarity
    return sorted(lesson_recommendations.values(), key=lambda x: (-x['count'], -x['similarity']))
