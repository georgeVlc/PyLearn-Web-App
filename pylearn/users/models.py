from django.db import models
from django.contrib.auth.models import User
from lessons.models import Lesson, Quiz, Task

# Create your models here.

class UserProgress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    completed_lessons = models.ManyToManyField(Lesson, blank=True)  # completed lessons
    quiz_attempts = models.ManyToManyField(Quiz, through='QuizAttempt')  # quiz attempts
    completed_tasks = models.ManyToManyField(Task, blank=True)  # New field

    def __str__(self):
        return f"{self.user.username}'s Progress"

class QuizAttempt(models.Model):
    user_progress = models.ForeignKey(UserProgress, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    points = models.IntegerField()
    attempts = models.IntegerField(default=1)  # number of retries
    passed = models.BooleanField(default=False)

    def __str__(self):
        return f"Attempt by {self.user_progress.user.username} on {self.quiz}"

class TaskAttempt(models.Model):
    user_progress = models.ForeignKey(UserProgress, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    points = models.IntegerField()
    accuracy = models.FloatField(default=0.0)
    attempts = models.IntegerField(default=1)  # number of retries
    passed = models.BooleanField(default=False)

    def __str__(self):
        return f"Attempt by {self.user_progress.user.username} on {self.task}"
