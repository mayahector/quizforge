"""
Outbound webhook notifications. Fires a JSON POST to
settings.QUIZ_COMPLETION_WEBHOOK_URL whenever a learner finishes a quiz
attempt — useful for piping results into Slack, Discord, or any other
service with an incoming-webhook endpoint.

Disabled by default: leave QUIZ_COMPLETION_WEBHOOK_URL unset (see
.env.example) and this becomes a no-op.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_quiz_completion_webhook(attempt):
    url = getattr(settings, "QUIZ_COMPLETION_WEBHOOK_URL", "")
    if not url:
        return

    summary = (
        f'{attempt.user.username} scored {attempt.score_percentage}% on '
        f'"{attempt.quiz.title}" '
        f"({'passed' if attempt.passed else 'did not pass'})."
    )
    payload = {
        "event": "quiz.completed",
        "text": summary,  # a "text" field is understood by Slack/Discord
        "user": attempt.user.username,
        "quiz": attempt.quiz.title,
        "quiz_slug": attempt.quiz.slug,
        "score": attempt.score,
        "score_percentage": attempt.score_percentage,
        "passed": attempt.passed,
        "completed_at": (
            attempt.completed_at.isoformat() if attempt.completed_at else None
        ),
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=getattr(settings, "WEBHOOK_TIMEOUT_SECONDS", 3.0),
        )
        response.raise_for_status()
    except requests.RequestException:
        # A webhook delivery failure should never break the learner-facing
        # request that triggered it (e.g. viewing their results page).
        logger.warning(
            "Quiz completion webhook delivery failed for attempt %s",
            attempt.pk,
            exc_info=True,
        )
