from django.shortcuts import render
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from .models import UserProgress, QuizAttempt, TaskAttempt
from lessons.models import chapter_size
from django.contrib.auth import authenticate, login,  logout
from django.contrib.auth import authenticate, login as auth_login 
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Avg, Count, Sum, Q, F
from django.contrib.auth.decorators import login_required
from lessons.models import Lesson, Quiz
from math import ceil
from lessons.utils import get_chapter_number_for_lesson
from .utils import *
# Create your views here.

@login_required
def view_users(request):
    users = User.objects.all()  # List users
    return render(request, 'view_users.html', {'users': users})

@login_required
def view_user_attempts(request, user_id):
    user_progress = get_object_or_404(UserProgress, user_id=user_id)
    quiz_lessons = get_quiz_lessons(user_progress)
    task_lessons = get_task_lessons(user_progress)

    all_lessons = list(quiz_lessons) + list(task_lessons)
    total_points_earned = 0
    
    total_points_earned += process_quiz_lessons(quiz_lessons, user_progress)
    total_points_earned += process_task_lessons(task_lessons, user_progress)
    
    overall_accuracy, total_attempts_count, total_lessons_passed = calculate_overall_stats(quiz_lessons, task_lessons)  
 
    context = {
        'user_progress': user_progress,
        'quiz_lessons': quiz_lessons,
        'task_lessons': task_lessons,
        'overall_accuracy': overall_accuracy,
        'total_attempts_count': total_attempts_count,
        'total_lessons_passed': total_lessons_passed,
        'total_points_earned': total_points_earned
    }

    return render(request, 'view_user_attempts.html', context)
    
def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
        else:
            user = User.objects.create_user(username=username, password=password)
            user.save()
            messages.success(request, 'Account created successfully!')
            return redirect('users:login')
    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            if not UserProgress.objects.filter(user=user).exists():
                UserProgress.objects.create(user=user)
            return redirect('home')  # Redirect to the home page
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

