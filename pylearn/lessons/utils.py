import os
import json
from .models import Lesson, Quiz
from django.db.utils import OperationalError


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
                lesson_title = (' ').join(lesson_tokens[1:])
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
