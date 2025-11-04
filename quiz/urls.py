# quiz/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('quiztypes/', views.QuizTypeListView.as_view(), name='quiztype_list'),
    path('quiztypes/create/', views.QuizTypeCreateView.as_view(), name='quiztype_create'),
    path('quiztypes/<int:pk>/edit/', views.QuizTypeUpdateView.as_view(), name='quiztype_edit'),
    path('quiztypes/<int:pk>/delete/', views.QuizTypeDeleteView.as_view(), name='quiztype_delete'),
    path('questions/', views.QuestionListView.as_view(), name='question_list'),
    path('questions/create/', views.QuestionCreateView.as_view(), name='question_create'),
    path('questions/<int:pk>/edit/', views.QuestionUpdateView.as_view(), name='question_edit'),
    path('questions/<int:pk>/delete/', views.QuestionDeleteView.as_view(), name='question_delete'),
    path('questions/<int:pk>/start/', views.GenerateQuiz, name='start_quiz'),
    path('upload-quiz/', views.upload_quiz_from_word, name='upload_quiz_from_word'),

]