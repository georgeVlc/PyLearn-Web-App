import os
import json
import random
from .models import Lesson, Quiz, Task, chapter_size
from users.models import UserProgress, QuizAttempt, TaskAttempt
from .code_eval import *
from django.utils.timezone import now

    
def load_local_data():
    lessons_path = "lessons/templates/lessons_html/"
    tests_path = "lessons/data/lessons_tests/"
    
    try:
        # Iterate through all lesson HTML files
        for lesson_file in os.listdir(lessons_path):
            if lesson_file.endswith(".html"):
                lesson_tokens = lesson_file.split(".") # Splitting the lesson file-name on '.'
                lesson_tokens = lesson_tokens[0].split("_") # Splitting on '_' and excluding the file extention
                lesson_id = int(lesson_tokens[0])  # Extract lesson ID from filename
                lesson_title = ' '.join([token.capitalize() for token in lesson_tokens[1:]])  # Capitalize each token
                
                # Load lesson content                
                with open(os.path.join(lessons_path, lesson_file), "r") as file:
                    content = file.read()

                is_task_based = is_task_based_lesson(lesson_title)
                # Create or update the lesson in the database
                lesson, created = Lesson.objects.update_or_create(
                    id=lesson_id,
                    defaults={
                        "title": lesson_title,
                        "content": content,
                        "order": lesson_id,
                        "is_task_based": is_task_based,
                    },
                )

                # Load test for this lesson
                test_file_path = os.path.join(tests_path, f"{('_').join(lesson_tokens)}.json")
                with open(test_file_path, "r") as file:
                    test_data = json.load(file)
                
                if lesson.is_task_based:
                    # Load tasks
                    for task in test_data:
                        Task.objects.update_or_create(
                            lesson=lesson,
                            description=task["description"],
                            code_stub=task["code_stub"],
                            correct_code=task["correct_code"],
                            expected_output=task["expected_output"],
                            points=task["points"]
                        )
                        print(f'{task["points"]=}')
                else:
                    # Load quizzes
                    for quiz in test_data:
                        Quiz.objects.update_or_create(
                            lesson=lesson,
                            question=quiz["question"],
                            defaults={
                                "answer_choices": quiz["answer_choices"],
                                "correct_answer": quiz["correct_answer"],
                            },
                            points=quiz["points"]
                        )
                        print(f'{quiz["points"]=}')
    except Exception as e:
        print("Database not ready. Skipping lesson preloading." + e)
        # Path to lessons and quizzes data

def delete_all_lessons_quizzes_tasks():
    Quiz.objects.all().delete()
    Task.objects.all().delete()
    Lesson.objects.all().delete()
    print("All lessons quizzes and tasks have been deleted from the database.")

def get_chapter_number_for_lesson(lesson_id):
    lesson = Lesson.objects.get(id=lesson_id)
    lessons = Lesson.objects.order_by('order')
    chapter_number = 1
    for idx, lesson_in_chapter in enumerate(lessons):
        if lesson_in_chapter.id == lesson.id:
            return (idx // chapter_size) + 1
    return None

def calculate_xp(lesson_id, lesson_title):
    if is_task_based_lesson(lesson_title):
        lower = 50 + lesson_id * 2
        upper = 75 + lesson_id * 3
    else:        
        lower = 10 + lesson_id * 1
        upper = 15 + lesson_id * 2
        
    return random.randint(lower, upper)

def update_quiz_attempts(request, quizzes, user_progress, lesson):
    lesson_attempts = QuizAttempt.objects.filter(
        user_progress=user_progress, quiz__lesson=lesson
    ).values('user_progress').distinct().count()
    
    info = []
    for quiz in quizzes:
        user_answer_key = request.POST.get(f'quiz_{quiz.id}')  # Key chosen by user
        correct_answer_key = quiz.correct_answer  # Key for the correct answer
        passed = user_answer_key == correct_answer_key

        # Update or create quiz attempts
        existing_attempt = QuizAttempt.objects.filter(user_progress=user_progress, quiz=quiz).first()
        if existing_attempt:
            existing_attempt.points = quiz.points if passed else 0
            existing_attempt.passed = passed
            existing_attempt.attempts = lesson_attempts  # Track by lesson attempt
            existing_attempt.created_at = now()
            existing_attempt.save()
        else:
            QuizAttempt.objects.create(
                user_progress=user_progress,
                quiz=quiz,
                points=quiz.points if passed else 0,
                passed=passed,
                attempts=lesson_attempts,
                created_at=now()
            ) 
        info.append({
            'user_answer_key': user_answer_key,
            'passed': passed,
            'points': quiz.points
        })   
    return info

def update_task_attempts(request, tasks, user_progress, lesson):
    lesson_attempts = TaskAttempt.objects.filter(
        user_progress=user_progress, task__lesson=lesson
    ).values('user_progress').distinct().count()
    
    info = []
    for task in tasks:
        user_code = request.POST['task_code']
        accuracy = evaluate_code(user_code, task.correct_code)
        print(f'{accuracy=}')
        passed = 1 if accuracy >= 50 else 0
                        
        existing_attempt = TaskAttempt.objects.filter(user_progress=user_progress, task=task).first()
        if existing_attempt:
            existing_attempt.points = task.points if passed else 0
            existing_attempt.passed = passed
            existing_attempt.attempts = lesson_attempts  # Track by lesson attempt
            existing_attempt.created_at = now()
            existing_attempt.save()
        else:
            TaskAttempt.objects.create(
                user_progress=user_progress,
                task=task,
                points=task.points if passed else 0,
                accuracy=accuracy,
                passed=passed,
                attempts=lesson_attempts,
                created_at=now()
            )    
        info.append({
            'user_code': user_code,
            'accuracy': accuracy,
            'passed': passed,
            'points': task.points
        })
    return info 
    
def track_quiz_test_results(request, quizzes, info):
    correct_count = 0
    mistakes = []
    
    for i, quiz in enumerate(quizzes):
        user_answer_key = info[i]['user_answer_key']
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
                },
                'points': quiz.points
            })
    return correct_count, mistakes

def track_task_test_results(request, tasks, info):
    correct_count = 0
    results = []
    
    for i, task in enumerate(tasks):
        user_code = info[i]['user_code']
        print(f'USER CODE: {user_code}')
        correct_code = task.correct_code
        task_accuracy = info[i]['accuracy']
        passed = info[i]['passed']
        
        if passed:
            correct_count += 1

        results.append({
            'task': f'task {i}',
            'user_answer': user_code,
            'correct_answer': correct_code,
            'feedback': generate_feedback(user_code, correct_code, task_accuracy),
            'accuracy': task_accuracy,
            'points': task.points
        })
        
    return correct_count, results

def is_recap_lesson(lesson):
    return "recap" in lesson.title.lower()

def is_task_based_lesson(lesson_title):
    return ("project" in lesson_title.lower()) == True

def match_question_to_lessons(question, lessons):
    """
    Match a quiz question to the most relevant lessons.
    """
    best_match = None
    best_points = 0

    for lesson in lessons:
        similarity = SequenceMatcher(None, question.lower(), lesson.title.lower()).ratio()
        if similarity > best_points:
            best_points = similarity
            best_match = lesson

    return best_match, best_points

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
