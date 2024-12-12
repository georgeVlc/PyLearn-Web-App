"""
URL configuration for pylearn project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from users import views as user_views  # Import user views
from lessons import views as lesson_views  # Import lesson views
from . import views as pylearn_views  # Import views from pylearn package itself

urlpatterns = [
    path('', pylearn_views.home, name='home'),
    path('users/', include('users.urls')),  # Include the users URLs
    path('users/view_users/', user_views.view_users, name='view_users'),
    path('users/view_user_attempts/<int:user_id>/', user_views.view_user_attempts, name='view_user_attempts'),
    path('lessons/', include('lessons.urls')),  # Include the lessons URLs
    path('lessons/view_lessons/', lesson_views.view_lessons, name='view_lessons'),
]
