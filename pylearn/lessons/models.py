from django.db import models

# Create your models here.
chapter_size = 10
chapter_titles = ['Python Basics', 'Python Advanced', 'Python Modules', 'Python Hands On']
chapter_difficulties = ['Easy', 'Intermidiate', 'Advanced', 'Mixed']

class Lesson(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()  # HTML or Markdown for lesson content
    order = models.IntegerField()  # Lesson order in the curriculum
    is_task_based = models.BooleanField(default=False)  # True for tasks, False for quizzes

    def __str__(self):
        print(f'Title: {self.title}\nContent: {self.content}')
        return self.title

class Quiz(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="quizzes")
    question = models.TextField()
    answer_choices = models.JSONField()  # Store multiple choices as JSON
    correct_answer = models.CharField(max_length=100)

    def __str__(self):
        return f"Quiz for {self.lesson.title}"

class Task(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="tasks")
    description = models.TextField()  # Description of the task
    code_stub = models.TextField(blank=True, null=True)  # Starter code for the user
    correct_code = models.TextField()  # The correct solution for the task
    expected_output = models.TextField()  # Expected output after running correct code

    def __str__(self):
        return f"Task for {self.lesson.title}"
