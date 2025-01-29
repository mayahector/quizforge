from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Profile


class ProfileSignalTests(TestCase):
    def test_profile_is_created_automatically_for_new_user(self):
        user = User.objects.create_user(
            "alice", "alice@example.com", "pw12345!"
        )
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertEqual(user.profile.role, Profile.Role.STUDENT)

    def test_saving_an_existing_user_without_profile_backfills_one(self):
        user = User.objects.create_user("bob", "bob@example.com", "pw12345!")
        Profile.objects.filter(user=user).delete()
        user.save()
        self.assertTrue(Profile.objects.filter(user=user).exists())


class RegistrationViewTests(TestCase):
    def test_register_creates_user_with_chosen_role(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "new_learner",
                "email": "learner@example.com",
                "password1": "S3cure-Pass!23",
                "password2": "S3cure-Pass!23",
                "role": Profile.Role.INSTRUCTOR,
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="new_learner")
        self.assertEqual(user.profile.role, Profile.Role.INSTRUCTOR)
        # Registering also logs the user in.
        self.assertIn("_auth_user_id", self.client.session)

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "oops",
                "email": "oops@example.com",
                "password1": "S3cure-Pass!23",
                "password2": "totally-different",
                "role": Profile.Role.STUDENT,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="oops").exists())


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "carol", "carol@example.com", "pw12345!"
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_authenticated_user_can_view_and_edit_profile(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("accounts:profile-edit"), {"bio": "Loves quizzes."}
        )
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, "Loves quizzes.")
