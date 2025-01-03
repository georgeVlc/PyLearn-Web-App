from django.apps import AppConfig

class LessonsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lessons'

    def ready(self):
        try:
            from .utils import load_local_data, delete_all_lessons_quizzes_tasks
            from users.utils import delete_all_progress_and_attempts
            # delete_all_progress_and_attempts()
            # delete_all_lessons_quizzes_tasks()
            # load_local_data()
        except Exception as e:
            print(f"Error during lesson preloading: {e}")
