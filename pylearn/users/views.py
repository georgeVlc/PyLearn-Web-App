from django.shortcuts import render
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from .models import UserProgress, QuizAttempt
from django.contrib.auth import authenticate, login,  logout
from django.contrib.auth import authenticate, login as auth_login 
from django.shortcuts import render, redirect
from django.contrib import messages

# Create your views here.

def view_users(request):
    users = User.objects.all()  # List users
    return render(request, 'view_users.html', {'users': users})

def view_user_attempts(request, user_id):
    user_progress = get_object_or_404(UserProgress, user_id=user_id)
    attempts = QuizAttempt.objects.filter(user_progress=user_progress)  # get all quiz attempts for the user's progress
    return render(request, 'view_user_attempts.html', {
        'attempts': attempts,
        'user_progress': user_progress,
    })
    
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