from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        try:
            from .utils import delete_all_progress_and_attempts
            # delete_all_progress_and_attempts()
        except Exception as e:
            print(f"Error during model preloading: {e}")
