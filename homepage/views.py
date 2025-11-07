from django.shortcuts import render, redirect
from quiz.models import GenerateQuizQuestion, AnswerUsers, GenerateQuiz

# Create your views here.
def home(request):
    if request.user.is_authenticated:
        my_test = GenerateQuiz.objects.filter(user=request.user).order_by('-numbers')
        context = {'my_test': my_test}


        return render(request, 'index.html', context)
    else:
        return redirect('login')