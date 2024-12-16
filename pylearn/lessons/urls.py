from django.urls import path
from . import views

app_name = 'lessons'

urlpatterns = [
    path('view_lessons/', views.view_lessons, name='view_lessons'),
    path('view_lesson_test/<int:lesson_id>/', views.view_lesson_test, name='view_lesson_test'),
]
