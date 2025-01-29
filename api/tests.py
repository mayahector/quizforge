from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from quizzes.models import Category, Choice, Question, Quiz, QuizAttempt


class QuizApiTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Python Basics")
        self.quiz = Quiz.objects.create(
            title="Python Fundamentals",
            category=self.category,
            is_published=True,
        )
        self.question = Question.objects.create(
            quiz=self.quiz, text="2+2=?", order=1
        )
        self.correct = Choice.objects.create(
            question=self.question, text="4", is_correct=True
        )
        Choice.objects.create(
            question=self.question, text="5", is_correct=False
        )

    def test_quiz_list_is_public(self):
        response = self.client.get("/api/quizzes/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)

    def test_quiz_detail_never_leaks_is_correct(self):
        response = self.client.get(f"/api/quizzes/{self.quiz.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("is_correct", response.content.decode())

    def test_unpublished_quiz_is_hidden_from_the_api(self):
        Quiz.objects.create(
            title="Draft Quiz", category=self.category, is_published=False
        )
        response = self.client.get("/api/quizzes/")
        titles = [q["title"] for q in response.json()["results"]]
        self.assertNotIn("Draft Quiz", titles)


class MyAttemptsApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "learner", "learner@example.com", "pw12345!"
        )
        category = Category.objects.create(name="Python Basics")
        self.quiz = Quiz.objects.create(
            title="Python Fundamentals", category=category, is_published=True
        )

    def test_requires_authentication(self):
        response = self.client.get("/api/my-attempts/")
        self.assertEqual(response.status_code, 403)

    def test_only_returns_the_requesting_users_attempts(self):
        other_user = User.objects.create_user("other", password="pw12345!")
        QuizAttempt.objects.create(user=other_user, quiz=self.quiz)
        mine = QuizAttempt.objects.create(user=self.user, quiz=self.quiz)

        self.client.force_login(self.user)
        response = self.client.get("/api/my-attempts/")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], mine.id)


class LeaderboardApiTests(TestCase):
    def test_requires_authentication(self):
        response = self.client.get(reverse("api:leaderboard"))
        self.assertEqual(response.status_code, 403)

    def test_returns_empty_list_with_no_completed_attempts(self):
        user = User.objects.create_user("learner", password="pw12345!")
        self.client.force_login(user)
        response = self.client.get(reverse("api:leaderboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
