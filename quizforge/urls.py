"""
URL configuration for the QuizForge project.

Routes are namespaced per app: `accounts` for authentication, `quizzes` for
the learner/instructor-facing site, and `api` for the DRF-powered REST API.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("api/", include("api.urls")),
    path("", include("quizzes.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
