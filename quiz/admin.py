from django.contrib import admin
from .models import (
    QuizType, Question, Answer,
    GenerateQuiz, GenerateQuizQuestion,
    AnswerUsers
)


# --- 1️⃣ Test turi ---
@admin.register(QuizType)
class QuizTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('id',)
    list_editable = ('is_active',)


# --- 2️⃣ Savollar ---
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    fields = ('name', 'is_correct', 'is_active')
    show_change_link = True


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'quiz_type', 'is_multiple_choice', 'is_active')
    list_filter = ('quiz_type', 'is_multiple_choice','is_active')
    search_fields = ('name', 'quiz_type__name')
    inlines = [AnswerInline]
    ordering = ('id',)
    list_editable = ('is_active',)


# --- 3️⃣ Javoblar ---
@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'question', 'is_correct', 'is_active')
    list_filter = ('is_correct',  'is_active', 'question__quiz_type')
    search_fields = ('name', 'question__name', 'question__quiz_type__name')
    list_editable = ('is_correct', 'is_active')
    ordering = ('question', 'id')


# --- 4️⃣ Foydalanuvchi testlari ---
class GenerateQuizQuestionInline(admin.TabularInline):
    model = GenerateQuizQuestion
    extra = 0
    fields = ('question',)
    show_change_link = True


@admin.register(GenerateQuiz)
class GenerateQuizAdmin(admin.ModelAdmin):
    list_display = ('id', 'numbers', 'user', 'quiz_type', 'score', 'created', 'finished')
    list_filter = ('quiz_type', 'created', 'finished')
    search_fields = ('numbers', 'user__username', 'quiz_type__name')
    ordering = ('-created',)
    inlines = [GenerateQuizQuestionInline]


# --- 5️⃣ Testdagi savollar ---
@admin.register(GenerateQuizQuestion)
class GenerateQuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'quiz', 'question')
    list_filter = ('quiz__quiz_type',)
    search_fields = ('quiz__numbers', 'question__name', 'quiz__user__username')
    ordering = ('id',)


# --- 6️⃣ Foydalanuvchi javoblari ---
@admin.register(AnswerUsers)
class AnswerUsersAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'generate_quiz', 'question', 'answer')
    list_filter = ('generate_quiz__quiz_type', 'user',)
    search_fields = (
        'user__username',
        'generate_quiz__numbers',
        'question__name',
        'answer__name'
    )
    ordering = ('id',)
