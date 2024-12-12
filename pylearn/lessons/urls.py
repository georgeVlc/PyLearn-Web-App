from django.urls import path
from . import views

app_name = 'lessons'

urlpatterns = [
    path('view_lessons/', views.view_lessons, name='view_lessons'),
]
