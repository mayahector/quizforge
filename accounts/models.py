from django.conf import settings
from django.db import models


class Profile(models.Model):
    """
    Extends Django's built-in User with the extra fields QuizForge needs,
    without replacing the auth system. Created automatically for every new
    user via the post_save signal in accounts.signals.
    """

    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        INSTRUCTOR = "instructor", "Instructor"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.STUDENT
    )
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_instructor(self):
        return self.role == self.Role.INSTRUCTOR
