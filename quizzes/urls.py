from django.urls import path

from . import views

app_name = "quizzes"

urlpatterns = [
    path("", views.quiz_list, name="quiz-list"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
]
