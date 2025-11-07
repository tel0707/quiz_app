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
    path('questions/<int:pk>/start/', views.generate_quiz, name='start_quiz'),
    path('upload-quiz/', views.upload_quiz_from_word, name='upload_quiz_from_word'),
    path('quiz/<int:quiz_id>/page/<int:page>/', views.quiz_page, name='quiz_page'),
    path('quiz/save-answer/', views.save_answer, name='save_answer'),
    path('quiz/finish/', views.finish_quiz, name='finish_quiz'),
# Auth
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('signup/', views.user_signup, name='signup'),

]