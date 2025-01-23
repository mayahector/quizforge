"""
Shared business logic that both the Django views and the REST API need,
kept out of views.py so it isn't duplicated between the two front ends.
"""

from collections import defaultdict

from django.contrib.auth import get_user_model

from .models import QuizAttempt


def compute_leaderboard(limit=20):
    """
    Rank learners by the average of their best score per quiz, across every
    quiz they've completed at least once. Retaking one quiz repeatedly can't
    be farmed for rank since only the best attempt per quiz counts.

    Returns a list of dicts: rank, user, quizzes_completed, average_score.
    """
    completed = QuizAttempt.objects.filter(
        status=QuizAttempt.Status.COMPLETED
    ).values("user_id", "quiz_id", "score_percentage")

    best_per_user_quiz = {}
    for row in completed:
        key = (row["user_id"], row["quiz_id"])
        best = best_per_user_quiz.get(key)
        if best is None or row["score_percentage"] > best:
            best_per_user_quiz[key] = row["score_percentage"]

    scores_by_user = defaultdict(list)
    for (user_id, _quiz_id), score in best_per_user_quiz.items():
        scores_by_user[user_id].append(score)

    rankings = [
        {
            "user_id": user_id,
            "quizzes_completed": len(scores),
            "average_score": round(sum(scores) / len(scores), 1),
        }
        for user_id, scores in scores_by_user.items()
    ]
    rankings.sort(
        key=lambda r: (-r["average_score"], -r["quizzes_completed"])
    )
    top_rankings = rankings[:limit]

    users = get_user_model().objects.in_bulk(
        [r["user_id"] for r in top_rankings]
    )
    for position, entry in enumerate(top_rankings, start=1):
        entry["rank"] = position
        entry["user"] = users[entry["user_id"]]

    return top_rankings
