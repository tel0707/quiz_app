# quiz/urls.py
from django.urls import path
from . import views

urlpatterns = [

    path('quiztypes/', views.QuizTypeListView.as_view(), name='quiztype_list'),
    path('quiztypes/create/', views.QuizTypeCreateView.as_view(), name='quiztype_create'),
    path('quiztypes/<slug:slug>/edit/', views.QuizTypeUpdateView.as_view(), name='quiztype_edit'),
    path('quiztypes/<slug:slug>/delete/', views.QuizTypeDeleteView.as_view(), name='quiztype_delete'),
    path('questions/', views.QuestionListView.as_view(), name='question_list'),
    path('questions/create/', views.QuestionCreateView.as_view(), name='question_create'),
    path('questions/<slug:slug>/edit/', views.QuestionUpdateView.as_view(), name='question_edit'),
    path('questions/<slug:slug>/delete/', views.QuestionDeleteView.as_view(), name='question_delete'),
    path('questions/<slug:slug>/start/', views.generate_quiz, name='start_quiz'),
    path('upload-quiz/', views.upload_quiz_from_word, name='upload_quiz_from_word'),
    path('quiz/<slug:quiz_slug>/page/<int:page>/', views.quiz_page, name='quiz_page'),
    path('quiz/save-answer/', views.save_answer, name='save_answer'),
    path('quiz/finish/', views.finish_quiz, name='finish_quiz'),
    path('result_users/<slug:quiz_slug>/', views.result_users, name='result_users'),
    path('all-results/', views.all_quiz_results, name='all_quiz_results'),
    path('all-results/export/', views.export_results_excel, name='export_results_excel'),
# Auth
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('signup/', views.user_signup, name='signup'),

]
