# QuizForge

**QuizForge** is a full-stack Django quiz management platform. Instructors
author categorized, timed quizzes in the Django admin; learners take them,
get instantly graded, track their progress on a personal dashboard, and
compete on a leaderboard. A DRF REST API sits alongside the server-rendered
frontend, and quiz completions can optionally notify an outbound webhook
(Slack, Discord, or any other JSON-accepting endpoint).

## Features

- **Accounts** — registration, login/logout, password change, and a
  student/instructor profile with bio and avatar.
- **Quiz catalog** — published quizzes browsable by category, with
  difficulty badges, question counts, and time limits.
- **Timed quiz-taking engine** — one question at a time, a live countdown
  that auto-submits when time runs out, and idempotent grading.
- **Results & dashboard** — a per-question answer breakdown, pass/fail
  against a configurable threshold, and a personal dashboard with
  aggregate stats and a Chart.js score-trend line chart.
- **Leaderboard** — ranked by each learner's *average best score per quiz*,
  so retaking one quiz repeatedly can't be farmed for rank.
- **REST API** (`/api/`) — read-only endpoints for categories, quizzes
  (never leaking correct answers before submission), a learner's own
  attempt history, and the leaderboard.
- **Outbound webhooks** — POST a JSON summary to any incoming-webhook URL
  when a quiz attempt completes. Disabled by default.
- **Django admin** — inline question/choice authoring, prepopulated slugs,
  filters, and read-only attempt inspection.

## Tech stack

Django 6, Django REST Framework, django-environ, SQLite (dev) /
any `DATABASE_URL`-compatible database (prod), Bootstrap 5, Chart.js.

## Getting started

```bash
git clone <this-repo>
cd Maya

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # adjust values as needed

python manage.py migrate
python manage.py seed_demo_data    # optional: sample categories/quizzes
python manage.py createsuperuser   # optional: your own admin account

python manage.py runserver
```

Visit `http://127.0.0.1:8000/` for the app and `/admin/` to author quizzes.
If you ran `seed_demo_data`, log in with `instructor` /
`quizforge-demo` (change the password immediately outside of a demo).

## Configuration

All settings are environment-driven via `django-environ` — see
`.env.example` for the full list. Notably:

| Variable | Purpose |
|---|---|
| `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` | Standard Django settings |
| `DATABASE_URL` | Defaults to local SQLite; point at Postgres etc. in production |
| `QUIZ_COMPLETION_WEBHOOK_URL` | Set to an incoming-webhook URL to enable quiz-completion notifications |
| `WEBHOOK_TIMEOUT_SECONDS` | HTTP timeout for the webhook request (default `3.0`) |

## Running tests

```bash
python manage.py test
```

## Project structure

```
quizforge/    Project settings, root URLconf, WSGI/ASGI entrypoints
accounts/     Auth: registration, login, profile
quizzes/      Domain: categories, quizzes, questions, attempts, scoring,
              the quiz-taking engine, dashboard, leaderboard, webhooks
api/          DRF serializers/viewsets exposing quizzes/ over REST
templates/    Server-rendered frontend (Bootstrap 5)
static/       Project CSS
```

## Deployment

The project is a standard Django app: set `DEBUG=False`, a real
`SECRET_KEY`, `ALLOWED_HOSTS`, and a production `DATABASE_URL` via
environment variables, run `python manage.py collectstatic --noinput`,
and serve `quizforge.wsgi:application` with your WSGI server of choice
(e.g. `pip install gunicorn` and `gunicorn quizforge.wsgi`).

## CI

GitHub Actions (`.github/workflows/ci.yml`) lints with flake8, checks for
missing migrations, and runs the test suite on every push and pull request
against `main`.
