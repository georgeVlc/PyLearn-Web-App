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


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum

@login_required
def view_users(request):
    users = User.objects.all()  # List all users
    user_points = []  # List to store each user's total points

    for user in users:
        try:
            user_progress = UserProgress.objects.get(user=user)  # Try to get the UserProgress
            quiz_lessons = get_quiz_lessons(user_progress)
            task_lessons = get_task_lessons(user_progress)

            total_points = 0
            total_points += process_quiz_lessons(quiz_lessons, user_progress)
            total_points += process_task_lessons(task_lessons, user_progress)

            user_points.append({
                'user': user,
                'total_points': total_points
            })
        except UserProgress.DoesNotExist:
            # If no UserProgress exists, assign 0 points and skip the user
            user_points.append({
                'user': user,
                'total_points': 0
            })
    
    # Sort users by total points in descending order
    user_points = sorted(user_points, key=lambda x: x['total_points'], reverse=True)
    
    # Find the rank of the current user
    current_user_points = next(item for item in user_points if item['user'] == request.user)
    current_user_rank = user_points.index(current_user_points) + 1  # Rank is 1-based index
    
    # Pass the sorted users and the current user's rank to the template
    context = {
        'user_points': user_points,
        'current_user_rank': current_user_rank
    }

    return render(request, 'view_users.html', context)

from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()  # Converts datetime to ISO 8601 string
        return super().default(obj)


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
    time_series_data = get_progress_time_series(user_id)
    quiz_data = time_series_data['quiz_progress']
    task_data = time_series_data['task_progress']
    quiz_data_serialized = json.dumps(quiz_data, cls=DateTimeEncoder)
    task_data_serialized = json.dumps(task_data, cls=DateTimeEncoder)

    context = {
        'user_progress': user_progress,
        'quiz_lessons': quiz_lessons,
        'task_lessons': task_lessons,
        'overall_accuracy': overall_accuracy,
        'total_attempts_count': total_attempts_count,
        'total_lessons_passed': total_lessons_passed,
        'total_points_earned': total_points_earned,
        'quiz_data': quiz_data_serialized,
        'task_data': task_data_serialized
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

