from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Category, Choice, Question, Quiz, QuizAttempt
from .services import compute_leaderboard


def make_quiz(**overrides):
    category = overrides.pop("category", None) or Category.objects.create(
        name="Python Basics"
    )
    defaults = {
        "title": "Python Fundamentals",
        "category": category,
        "is_published": True,
        "pass_percentage": 50,
    }
    defaults.update(overrides)
    return Quiz.objects.create(**defaults)


class ModelBehaviorTests(TestCase):
    def test_slugs_are_derived_from_title_and_name(self):
        category = Category.objects.create(name="General Knowledge")
        quiz = make_quiz(title="World Capitals", category=category)
        self.assertEqual(category.slug, "general-knowledge")
        self.assertEqual(quiz.slug, "world-capitals")

    def test_quiz_question_count_and_total_points(self):
        quiz = make_quiz()
        Question.objects.create(quiz=quiz, text="Q1", points=2)
        Question.objects.create(quiz=quiz, text="Q2", points=3)
        self.assertEqual(quiz.question_count, 2)
        self.assertEqual(quiz.total_points, 5)


class QuizAttemptScoringTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "learner", "learner@example.com", "pw12345!"
        )
        self.quiz = make_quiz(pass_percentage=50)
        self.q1 = Question.objects.create(
            quiz=self.quiz, text="2+2=?", order=1, points=1
        )
        self.q1_correct = Choice.objects.create(
            question=self.q1, text="4", is_correct=True
        )
        self.q1_wrong = Choice.objects.create(
            question=self.q1, text="5", is_correct=False
        )
        self.q2 = Question.objects.create(
            quiz=self.quiz, text="Capital of France?", order=2, points=1
        )
        self.q2_correct = Choice.objects.create(
            question=self.q2, text="Paris", is_correct=True
        )

    def test_finish_grades_correct_and_incorrect_answers(self):
        attempt = QuizAttempt.objects.create(user=self.user, quiz=self.quiz)
        attempt.answers.create(
            question=self.q1, selected_choice=self.q1_correct
        )
        attempt.answers.create(question=self.q2, selected_choice=None)

        attempt.finish()

        self.assertEqual(attempt.status, QuizAttempt.Status.COMPLETED)
        self.assertEqual(attempt.score, 1)
        self.assertEqual(attempt.score_percentage, 50.0)
        self.assertTrue(attempt.passed)

    def test_finish_is_idempotent(self):
        attempt = QuizAttempt.objects.create(user=self.user, quiz=self.quiz)
        attempt.answers.create(
            question=self.q1, selected_choice=self.q1_wrong
        )
        attempt.finish()
        first_completed_at = attempt.completed_at

        attempt.finish()  # calling again must not re-grade or re-fire
        self.assertEqual(attempt.completed_at, first_completed_at)

    def test_answer_is_correct_flag_tracks_selected_choice(self):
        attempt = QuizAttempt.objects.create(user=self.user, quiz=self.quiz)
        answer = attempt.answers.create(
            question=self.q1, selected_choice=self.q1_correct
        )
        self.assertTrue(answer.is_correct)

        answer.selected_choice = self.q1_wrong
        answer.save()
        self.assertFalse(answer.is_correct)


class QuizTakingFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "learner", "learner@example.com", "pw12345!"
        )
        self.quiz = make_quiz(pass_percentage=50)
        self.question = Question.objects.create(
            quiz=self.quiz, text="2+2=?", order=1
        )
        self.correct = Choice.objects.create(
            question=self.question, text="4", is_correct=True
        )
        self.client.force_login(self.user)

    def test_take_view_requires_login(self):
        self.client.logout()
        response = self.client.get(
            reverse("quizzes:quiz-take", args=[self.quiz.slug])
        )
        self.assertEqual(response.status_code, 302)

    def test_answering_the_only_question_completes_the_attempt(self):
        response = self.client.post(
            reverse("quizzes:quiz-take", args=[self.quiz.slug]),
            {"question_id": self.question.id, "choice": self.correct.id},
        )
        self.assertEqual(response.status_code, 302)

        attempt = QuizAttempt.objects.get(user=self.user, quiz=self.quiz)
        self.assertEqual(attempt.status, QuizAttempt.Status.IN_PROGRESS)

        # The redirect back to quiz-take is what actually finishes grading.
        self.client.get(reverse("quizzes:quiz-take", args=[self.quiz.slug]))
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, QuizAttempt.Status.COMPLETED)
        self.assertEqual(attempt.score_percentage, 100.0)

    @override_settings(
        QUIZ_COMPLETION_WEBHOOK_URL="https://hooks.example.com/incoming"
    )
    def test_completion_fires_webhook_when_configured(self):
        with patch("quizzes.webhooks.requests.post") as mock_post:
            self.client.post(
                reverse("quizzes:quiz-take", args=[self.quiz.slug]),
                {"question_id": self.question.id, "choice": self.correct.id},
            )
            self.client.get(
                reverse("quizzes:quiz-take", args=[self.quiz.slug])
            )
        self.assertTrue(mock_post.called)

    def test_completion_skips_webhook_when_not_configured(self):
        with patch("quizzes.webhooks.requests.post") as mock_post:
            self.client.post(
                reverse("quizzes:quiz-take", args=[self.quiz.slug]),
                {"question_id": self.question.id, "choice": self.correct.id},
            )
            self.client.get(
                reverse("quizzes:quiz-take", args=[self.quiz.slug])
            )
        self.assertFalse(mock_post.called)


class LeaderboardServiceTests(TestCase):
    def test_ranks_by_best_score_not_attempt_volume(self):
        quiz = make_quiz(pass_percentage=50)
        question = Question.objects.create(quiz=quiz, text="2+2=?")
        correct = Choice.objects.create(
            question=question, text="4", is_correct=True
        )
        wrong = Choice.objects.create(
            question=question, text="5", is_correct=False
        )

        strong = User.objects.create_user("strong", password="pw12345!")
        farmer = User.objects.create_user("farmer", password="pw12345!")

        # One perfect attempt.
        attempt = QuizAttempt.objects.create(user=strong, quiz=quiz)
        attempt.answers.create(question=question, selected_choice=correct)
        attempt.finish()

        # Many low-scoring attempts shouldn't outrank one good average.
        for _ in range(5):
            attempt = QuizAttempt.objects.create(user=farmer, quiz=quiz)
            attempt.answers.create(question=question, selected_choice=wrong)
            attempt.finish()

        rankings = compute_leaderboard()
        self.assertEqual(rankings[0]["user"].username, "strong")
        self.assertEqual(rankings[0]["average_score"], 100.0)
        self.assertEqual(rankings[1]["quizzes_completed"], 1)
