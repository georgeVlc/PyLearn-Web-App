from django.db import models

# Create your models here.

class Lesson(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()  # HTML or Markdown for lesson content
    order = models.IntegerField()  # Lesson order in the curriculum

    def __str__(self):
        return self.title

class Quiz(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="quizzes")
    question = models.TextField()
    answer_choices = models.JSONField()  # Store multiple choices as JSON
    correct_answer = models.CharField(max_length=100)

    def __str__(self):
        return f"Quiz for {self.lesson.title}"
