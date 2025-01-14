from django.contrib import admin

from .models import Answer, Category, Choice, Question, Quiz, QuizAttempt


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2
    min_num = 2


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    show_change_link = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "difficulty",
        "question_count",
        "is_published",
        "created_by",
        "created_at",
    )
    list_filter = ("is_published", "difficulty", "category")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [QuestionInline]
    autocomplete_fields = ["created_by"]

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "quiz", "order", "points")
    list_filter = ("quiz",)
    inlines = [ChoiceInline]


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ("question", "selected_choice", "is_correct", "answered_at")
    can_delete = False


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "quiz",
        "status",
        "score_percentage",
        "passed",
        "started_at",
        "completed_at",
    )
    list_filter = ("status", "passed", "quiz")
    search_fields = ("user__username", "quiz__title")
    readonly_fields = (
        "user",
        "quiz",
        "score",
        "score_percentage",
        "passed",
        "started_at",
        "completed_at",
    )
    inlines = [AnswerInline]
