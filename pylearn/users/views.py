from django.shortcuts import render
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from .models import UserProgress, QuizAttempt

# Create your views here.

def view_users(request):
    users = User.objects.all()  # List users
    return render(request, 'users/view_users.html', {'users': users})

def view_user_attempts(request, user_id):
    user_progress = get_object_or_404(UserProgress, user_id=user_id)
    attempts = user_progress.quiz_attempts.all()
    return render(request, 'users/view_user_attempts.html', {
        'attempts': attempts,
        'user_progress': user_progress,  # Include this in the context
    })
