from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def quiz_list(request):
    return render(request, "quizzes/quiz_list.html", {"quizzes": []})


@login_required
def dashboard(request):
    return render(request, "quizzes/dashboard.html")


@login_required
def leaderboard(request):
    return render(request, "quizzes/leaderboard.html")
