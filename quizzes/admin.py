from django.contrib import admin

from .models import Category, Choice, Question, Quiz


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
