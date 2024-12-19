from django.urls import path
from . import views

app_name = 'lessons'

urlpatterns = [
    path('view_chapters/', views.view_chapters, name='view_chapters'),
    path('chapter/<int:chapter_id>/lesson/<int:lesson_id>/', views.view_lessons, name='view_lessons'),
    path('view_lesson_test/<int:lesson_id>/', views.view_lesson_test, name='view_lesson_test'),
    path('take_lesson_test/<int:lesson_id>/', views.take_lesson_test, name='take_lesson_test'),
]
