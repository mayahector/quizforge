from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from quizzes.models import Category, Quiz, QuizAttempt
from quizzes.services import compute_leaderboard

from .serializers import (
    CategorySerializer,
    LeaderboardEntrySerializer,
    QuizAttemptSerializer,
    QuizDetailSerializer,
    QuizListSerializer,
)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quiz.objects.filter(is_published=True).select_related(
        "category"
    )
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return QuizDetailSerializer
        return QuizListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "retrieve":
            qs = qs.prefetch_related("questions__choices")
        category_slug = self.request.query_params.get("category")
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        return qs


class MyAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    """A learner's own quiz attempt history — never another user's."""

    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            QuizAttempt.objects.filter(user=self.request.user)
            .select_related("quiz")
            .order_by("-started_at")
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def leaderboard_view(request):
    rankings = compute_leaderboard(limit=20)
    serializer = LeaderboardEntrySerializer(rankings, many=True)
    return Response(serializer.data)
