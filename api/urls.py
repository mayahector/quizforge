from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "api"

router = DefaultRouter()
router.register("categories", views.CategoryViewSet, basename="category")
router.register("quizzes", views.QuizViewSet, basename="quiz")
router.register("my-attempts", views.MyAttemptViewSet, basename="my-attempt")

urlpatterns = [
    path("", include(router.urls)),
    path("leaderboard/", views.leaderboard_view, name="leaderboard"),
    # Adds a login/logout view for the browsable API UI at /api/.
    path("auth/", include("rest_framework.urls")),
]
