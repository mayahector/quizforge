from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from quizzes.models import Category, Choice, Question, Quiz

DEMO_CATALOG = {
    "Python Basics": [
        {
            "title": "Python Fundamentals",
            "difficulty": Quiz.Difficulty.EASY,
            "time_limit_minutes": 10,
            "pass_percentage": 60,
            "description": (
                "Variables, data types, and basic control flow."
            ),
            "questions": [
                {
                    "text": "What is the output of print(2 + 2)?",
                    "choices": [("4", True), ("22", False), ("Error", False)],
                },
                {
                    "text": "Which keyword defines a function in Python?",
                    "choices": [
                        ("func", False),
                        ("def", True),
                        ("function", False),
                    ],
                },
                {
                    "text": "Which of these is a mutable type?",
                    "choices": [
                        ("tuple", False),
                        ("str", False),
                        ("list", True),
                    ],
                },
            ],
        },
        {
            "title": "Django Essentials",
            "difficulty": Quiz.Difficulty.MEDIUM,
            "time_limit_minutes": 15,
            "pass_percentage": 70,
            "description": "Models, views, templates, and the ORM.",
            "questions": [
                {
                    "text": (
                        "Which file defines a Django app's URL routes "
                        "by convention?"
                    ),
                    "choices": [
                        ("routes.py", False),
                        ("urls.py", True),
                        ("views.py", False),
                    ],
                },
                {
                    "text": "What does the Django ORM let you avoid writing?",
                    "choices": [
                        ("HTML", False),
                        ("Raw SQL", True),
                        ("Python", False),
                    ],
                },
            ],
        },
    ],
    "General Knowledge": [
        {
            "title": "World Capitals",
            "difficulty": Quiz.Difficulty.EASY,
            "time_limit_minutes": 5,
            "pass_percentage": 60,
            "description": "A quick geography warm-up.",
            "questions": [
                {
                    "text": "What is the capital of France?",
                    "choices": [
                        ("Paris", True),
                        ("Lyon", False),
                        ("Marseille", False),
                    ],
                },
                {
                    "text": "What is the capital of Japan?",
                    "choices": [
                        ("Osaka", False),
                        ("Tokyo", True),
                        ("Kyoto", False),
                    ],
                },
            ],
        },
    ],
}


class Command(BaseCommand):
    help = (
        "Seed the database with demo categories, quizzes, questions, and "
        "an instructor account, so a fresh checkout has something to "
        "click through immediately. Safe to run more than once."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--instructor-password",
            default="quizforge-demo",
            help="Password for the seeded 'instructor' account.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        instructor, created = User.objects.get_or_create(
            username="instructor",
            defaults={"email": "instructor@example.com", "is_staff": True},
        )
        if created:
            instructor.set_password(options["instructor_password"])
            instructor.save()
            instructor.profile.role = instructor.profile.Role.INSTRUCTOR
            instructor.profile.save()
            self.stdout.write(
                self.style.SUCCESS(
                    "Created instructor account "
                    f"(username=instructor, "
                    f"password={options['instructor_password']})"
                )
            )

        quiz_count = 0
        for category_name, quizzes in DEMO_CATALOG.items():
            category, _ = Category.objects.get_or_create(name=category_name)
            for quiz_data in quizzes:
                quiz, quiz_created = Quiz.objects.get_or_create(
                    title=quiz_data["title"],
                    defaults={
                        "category": category,
                        "description": quiz_data["description"],
                        "difficulty": quiz_data["difficulty"],
                        "time_limit_minutes": quiz_data["time_limit_minutes"],
                        "pass_percentage": quiz_data["pass_percentage"],
                        "created_by": instructor,
                        "is_published": True,
                    },
                )
                if not quiz_created:
                    continue
                quiz_count += 1
                for order, question_data in enumerate(
                    quiz_data["questions"], start=1
                ):
                    question = Question.objects.create(
                        quiz=quiz, text=question_data["text"], order=order
                    )
                    for text, is_correct in question_data["choices"]:
                        Choice.objects.create(
                            question=question,
                            text=text,
                            is_correct=is_correct,
                        )

        self.stdout.write(
            self.style.SUCCESS(f"Seeded {quiz_count} new quiz(zes).")
        )
