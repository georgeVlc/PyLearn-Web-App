from django.shortcuts import render
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from .models import UserProgress, QuizAttempt
from django.contrib.auth import authenticate, login,  logout
from django.contrib.auth import authenticate, login as auth_login 
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Avg, Count, Sum, Q, F
from django.contrib.auth.decorators import login_required
from lessons.models import Lesson, Quiz
# Create your views here.

def view_users(request):
    users = User.objects.all()  # List users
    return render(request, 'view_users.html', {'users': users})

@login_required
def view_user_attempts(request, user_id):
    user_progress = get_object_or_404(UserProgress, user_id=user_id)

    # Group quiz attempts by lesson (test level)
    lessons_with_attempts = Lesson.objects.filter(
        quizzes__quizattempt__user_progress=user_progress
    ).annotate(
        total_attempts=Count('quizzes__quizattempt', distinct=True),
        total_quizzes=Count('quizzes', distinct=True)
    ).distinct()

    # Calculate lesson-level accuracy using a dictionary
    lesson_accuracy_dict = {}
    for lesson in lessons_with_attempts:
        user_correct_answers = QuizAttempt.objects.filter(
            user_progress=user_progress,
            quiz__lesson=lesson
        ).aggregate(total_correct=Sum('score'))['total_correct'] or 0

        total_attempts = lesson.total_attempts
        total_quizzes = lesson.total_quizzes
        
        # Calculate accuracy for each lesson
        lesson.accuracy = (
            (user_correct_answers / total_quizzes) * 100
            if total_attempts and total_quizzes > 0
            else 0
        )
        print(f'{(user_correct_answers / total_quizzes) * 100}')

    # Calculate overall stats across all lessons (quiz-level stats)
    overall_attempts = QuizAttempt.objects.filter(user_progress=user_progress)
    total_quizzes_attempted = overall_attempts.values('quiz').distinct().count()  # Distinct quizzes
    total_correct_answers = overall_attempts.aggregate(total_correct=Sum('score'))['total_correct'] or 0

    # Overall accuracy
    overall_accuracy = (
        (total_correct_answers / total_quizzes_attempted) * 100
        if total_quizzes_attempted > 0
        else 0
    )

    # Prepare context data
    context = {
        'user_progress': user_progress,
        'lessons_with_attempts': lessons_with_attempts,
        'overall_accuracy': overall_accuracy,
        'total_attempts_count': lessons_with_attempts.aggregate(total_attempts=Count('total_attempts'))['total_attempts'] or 0,
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

def logout_view(request):
    logout(request)
    return redirect('home')

