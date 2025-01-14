from django.urls import path

from . import views

app_name = "quizzes"

urlpatterns = [
    path("", views.quiz_list, name="quiz-list"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
    path("quiz/<slug:slug>/", views.quiz_detail, name="quiz-detail"),
    path("quiz/<slug:slug>/take/", views.quiz_take, name="quiz-take"),
    path(
        "attempt/<int:attempt_id>/results/",
        views.quiz_results,
        name="quiz-results",
    ),
]
