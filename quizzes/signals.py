from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import QuizAttempt
from .webhooks import send_quiz_completion_webhook


@receiver(post_save, sender=QuizAttempt)
def notify_quiz_completion(sender, instance, **kwargs):
    """
    Fire the completion webhook exactly once per finish() call. finish()
    sets the transient _just_completed flag right before saving so this
    handler can tell "just finished" apart from any other save on the row
    (e.g. an admin edit) without a second DB query.
    """
    if getattr(instance, "_just_completed", False):
        send_quiz_completion_webhook(instance)
        instance._just_completed = False
