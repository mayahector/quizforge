from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Quiz(models.Model):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="quizzes"
    )
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="quizzes_created",
    )
    difficulty = models.CharField(
        max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM
    )
    time_limit_minutes = models.PositiveIntegerField(
        default=10, help_text="Total time allowed to complete the quiz."
    )
    pass_percentage = models.PositiveIntegerField(
        default=60, help_text="Minimum score percentage to pass."
    )
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "quizzes"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("quizzes:quiz-detail", kwargs={"slug": self.slug})

    @property
    def question_count(self):
        return self.questions.count()

    @property
    def total_points(self):
        return sum(self.questions.values_list("points", flat=True))


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="questions"
    )
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text[:60]


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices"
    )
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text[:60]


class QuizAttempt(models.Model):
    """One learner's run through a quiz, from start to (optionally) finish."""

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )
    quiz = models.ForeignKey(
        Quiz, on_delete=models.CASCADE, related_name="attempts"
    )
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.IN_PROGRESS
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(null=True, blank=True)
    score_percentage = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user.username} · {self.quiz.title} ({self.status})"

    @property
    def deadline(self):
        return self.started_at + timedelta(
            minutes=self.quiz.time_limit_minutes
        )

    @property
    def is_expired(self):
        return (
            self.status == self.Status.IN_PROGRESS
            and timezone.now() >= self.deadline
        )

    @property
    def seconds_remaining(self):
        remaining = (self.deadline - timezone.now()).total_seconds()
        return max(0, int(remaining))

    def answered_question_ids(self):
        return set(self.answers.values_list("question_id", flat=True))

    def next_unanswered_question(self):
        answered_ids = self.answered_question_ids()
        return (
            self.quiz.questions.exclude(id__in=answered_ids)
            .order_by("order", "id")
            .first()
        )

    def finish(self):
        """Grade the attempt and mark it complete. Idempotent."""
        if self.status == self.Status.COMPLETED:
            return
        total_points = self.quiz.total_points or 1
        earned = sum(
            answer.question.points
            for answer in self.answers.select_related("question")
            if answer.is_correct
        )
        self.score = earned
        self.score_percentage = round((earned / total_points) * 100, 1)
        self.passed = self.score_percentage >= self.quiz.pass_percentage
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        # Read by the post_save handler in signals.py to fire the
        # completion webhook exactly once, without a second DB query.
        self._just_completed = True
        self.save()


class Answer(models.Model):
    """A learner's response to a single question within one attempt."""

    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers"
    )
    selected_choice = models.ForeignKey(
        Choice, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["attempt", "question"], name="one_answer_per_question"
            )
        ]

    def __str__(self):
        return f"Answer to {self.question_id} in attempt {self.attempt_id}"

    def save(self, *args, **kwargs):
        self.is_correct = bool(
            self.selected_choice and self.selected_choice.is_correct
        )
        super().save(*args, **kwargs)
