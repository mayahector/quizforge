from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Category, Quiz


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


@login_required
def quiz_take(request, slug):
    """Placeholder: the timed quiz-taking engine lands in the next commit."""
    quiz = get_object_or_404(Quiz, slug=slug, is_published=True)
    return render(request, "quizzes/quiz_take_stub.html", {"quiz": quiz})


@login_required
def dashboard(request):
    return render(request, "quizzes/dashboard.html")


@login_required
def leaderboard(request):
    return render(request, "quizzes/leaderboard.html")
