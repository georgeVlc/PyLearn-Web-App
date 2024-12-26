import os
import json
from .models import UserProgress, QuizAttempt, TaskAttempt
from django.db.utils import OperationalError


def delete_all_progress_and_attempts():
    UserProgress.objects.all().delete()
    QuizAttempt.objects.all().delete()
    TaskAttempt.objects.all().delete()
    print("All user progress and attempts have been deleted from the database.")
