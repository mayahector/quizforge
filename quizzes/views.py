from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Category, Choice, Quiz, QuizAttempt
from .services import compute_leaderboard


def quiz_list(request):
    quizzes = (
        Quiz.objects.filter(is_published=True)
        .select_related("category")
        .prefetch_related("questions")
    )

    category_slug = request.GET.get("category")
    if category_slug:
        quizzes = quizzes.filter(category__slug=category_slug)

    context = {
        "quizzes": quizzes,
        "categories": Category.objects.all(),
        "active_category": category_slug,
    }
    return render(request, "quizzes/quiz_list.html", context)


def quiz_detail(request, slug):
    quiz = get_object_or_404(
        Quiz.objects.select_related("category"), slug=slug, is_published=True
    )
    return render(request, "quizzes/quiz_detail.html", {"quiz": quiz})


def _get_active_attempt(user, quiz):
    """Return the learner's in-progress attempt for this quiz, expiring and
    creating one as needed so there is always exactly one live attempt."""
    attempt = (
        QuizAttempt.objects.filter(
            user=user, quiz=quiz, status=QuizAttempt.Status.IN_PROGRESS
        )
        .order_by("-started_at")
        .first()
    )
    if attempt and attempt.is_expired:
        attempt.finish()
        attempt = None
    if attempt is None:
        attempt = QuizAttempt.objects.create(user=user, quiz=quiz)
    return attempt


@login_required
def quiz_take(request, slug):
    quiz = get_object_or_404(Quiz, slug=slug, is_published=True)
    attempt = _get_active_attempt(request.user, quiz)

    if request.method == "POST":
        question_id = request.POST.get("question_id")
        choice_id = request.POST.get("choice")
        question = get_object_or_404(
            quiz.questions, id=question_id
        )
        choice = None
        if choice_id:
            choice = get_object_or_404(Choice, id=choice_id, question=question)
        attempt.answers.update_or_create(
            question=question, defaults={"selected_choice": choice}
        )
        return redirect("quizzes:quiz-take", slug=quiz.slug)

    if attempt.is_expired:
        attempt.finish()
        return redirect("quizzes:quiz-results", attempt_id=attempt.id)

    question = attempt.next_unanswered_question()
    if question is None:
        attempt.finish()
        return redirect("quizzes:quiz-results", attempt_id=attempt.id)

    answered_count = len(attempt.answered_question_ids())
    context = {
        "quiz": quiz,
        "attempt": attempt,
        "question": question,
        "answered_count": answered_count,
        "total_questions": quiz.question_count,
    }
    return render(request, "quizzes/quiz_take.html", context)


@login_required
def quiz_results(request, attempt_id):
    attempt = get_object_or_404(
        QuizAttempt.objects.select_related("quiz"),
        id=attempt_id,
        user=request.user,
    )
    if attempt.status != QuizAttempt.Status.COMPLETED:
        attempt.finish()

    answers = attempt.answers.select_related(
        "question", "selected_choice"
    ).order_by("question__order", "question__id")
    breakdown = [
        {
            "question": answer.question,
            "selected_choice": answer.selected_choice,
            "is_correct": answer.is_correct,
            "correct_choice": answer.question.choices.filter(
                is_correct=True
            ).first(),
        }
        for answer in answers
    ]

    context = {"attempt": attempt, "breakdown": breakdown}
    return render(request, "quizzes/quiz_results.html", context)


@login_required
def dashboard(request):
    completed = QuizAttempt.objects.filter(
        user=request.user, status=QuizAttempt.Status.COMPLETED
    ).select_related("quiz")

    stats = completed.aggregate(
        total_attempts=Count("id"),
        average_score=Avg("score_percentage"),
        passed_count=Count("id", filter=Q(passed=True)),
    )

    recent = completed.order_by("-completed_at")[:10]
    # Chart reads left-to-right chronologically, so reverse the recency order.
    chart_history = list(recent)[::-1]

    context = {
        "stats": stats,
        "recent_attempts": recent,
        "chart_labels": [a.quiz.title for a in chart_history],
        "chart_scores": [a.score_percentage for a in chart_history],
    }
    return render(request, "quizzes/dashboard.html", context)


@login_required
def leaderboard(request):
    rankings = compute_leaderboard(limit=20)
    return render(request, "quizzes/leaderboard.html", {"rankings": rankings})
