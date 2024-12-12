from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('view_users/', views.view_users, name='view_users'),
    path('view_user_attempts/<int:user_id>/', views.view_user_attempts, name='view_user_attempts'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
