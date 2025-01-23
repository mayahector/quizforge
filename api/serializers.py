from django.contrib.auth import get_user_model
from rest_framework import serializers

from quizzes.models import Category, Choice, Question, Quiz, QuizAttempt

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        # is_correct is intentionally excluded so the API never leaks
        # answers to a quiz that hasn't been submitted yet.
        fields = ["id", "text"]


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "order", "points", "choices"]


class QuizListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    question_count = serializers.ReadOnlyField()

    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "description",
            "difficulty",
            "time_limit_minutes",
            "pass_percentage",
            "question_count",
        ]


class QuizDetailSerializer(QuizListSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta(QuizListSerializer.Meta):
        fields = QuizListSerializer.Meta.fields + ["questions"]


class QuizAttemptSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)
    quiz_slug = serializers.CharField(source="quiz.slug", read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "quiz",
            "quiz_title",
            "quiz_slug",
            "status",
            "score",
            "score_percentage",
            "passed",
            "started_at",
            "completed_at",
        ]
        read_only_fields = fields


class LeaderboardEntrySerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    username = serializers.CharField(source="user.username")
    quizzes_completed = serializers.IntegerField()
    average_score = serializers.FloatField()
