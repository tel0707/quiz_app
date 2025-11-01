# quiz/views.py

from .forms import QuizTypeForm, QuestionForm, AnswerFormSet, AnswerUpdateFormSet

from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Question, QuizType
from django.db import transaction



# --- Ro‘yxat (hamma ko‘ra oladi) ---
class QuizTypeListView(ListView):
    model = QuizType
    template_name = 'quiz/quiztype_list.html'
    context_object_name = 'quiztypes'
    paginate_by = 10

    def get_queryset(self):
        return QuizType.objects.filter(is_active=True).order_by('-id')


# --- Superuser tekshiruvi ---
class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "Bu amalni faqat administrator bajarishi mumkin.")
        return super().handle_no_permission()


# --- Yaratish (faqat superuser) ---
class QuizTypeCreateView(SuperuserRequiredMixin, SuccessMessageMixin, CreateView):
    model = QuizType
    form_class = QuizTypeForm
    template_name = 'quiz/quiztype_form.html'
    success_url = reverse_lazy('quiztype_list')
    success_message = "Quiz turi muvaffaqiyatli qo‘shildi!"

    # ... oldingi kodlar ...

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        # Formset validligini tekshiramiz
        if not formset.is_valid():
            return self.form_invalid(form)

        # To'g'ri javoblar sonini hisoblaymiz
        correct_answers = [
            f for f in formset.forms
            if f.cleaned_data and not f.cleaned_data.get('DELETE', False) and f.cleaned_data.get('is_correct')
        ]

        if len(correct_answers) == 0:
            messages.error(self.request, "Kamida bitta to'g'ri javob bo'lishi kerak!")
            return self.form_invalid(form)

        # Agar hamma narsa yaxshi bo'lsa – saqlaymiz
        with transaction.atomic():
            self.object = form.save()
            formset.instance = self.object
            formset.save()

            # Oxirgi tanlangan quiz_type ni saqlash
            quiz_type_id = form.cleaned_data['quiz_type'].id
            self.request.session['last_quiztype_id'] = quiz_type_id

        return super().form_valid(form)


# --- Tahrirlash (faqat superuser) ---
class QuizTypeUpdateView(SuperuserRequiredMixin, SuccessMessageMixin, UpdateView):
    model = QuizType
    form_class = QuizTypeForm
    template_name = 'quiz/quiztype_form.html'
    success_url = reverse_lazy('quiztype_list')
    success_message = "Quiz turi muvaffaqiyatli yangilandi!"



    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if not formset.is_valid():
            return self.form_invalid(form)

        # Yangi va o'chirilmagan to'g'ri javoblarni hisoblaymiz
        correct_answers = [
            f for f in formset.forms
            if f.cleaned_data and not f.cleaned_data.get('DELETE', False) and f.cleaned_data.get('is_correct')
        ]

        if len(correct_answers) == 0:
            messages.error(self.request, "Kamida bitta to'g'ri javob bo'lishi kerak!")
            return self.form_invalid(form)

        with transaction.atomic():
            self.object = form.save()
            formset.instance = self.object
            formset.save()

            quiz_type_id = form.cleaned_data['quiz_type'].id
            self.request.session['last_quiztype_id'] = quiz_type_id

        return super().form_valid(form)


# --- O‘chirish (faqat superuser) ---
class QuizTypeDeleteView(SuperuserRequiredMixin, SuccessMessageMixin, DeleteView):
    model = QuizType
    template_name = 'quiz/quiztype_confirm_delete.html'
    success_url = reverse_lazy('quiztype_list')
    success_message = "Quiz turi muvaffaqiyatli o‘chirildi!"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


# Superuser tekshiruvi
class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "Bu amalni faqat administrator bajarishi mumkin.")
        return redirect('question_list')


# --- Savollar ro'yxati ---
class QuestionListView(ListView):
    model = Question
    template_name = 'quiz/question_list.html'
    context_object_name = 'questions'
    paginate_by = 10

    def get_queryset(self):
        return Question.objects.select_related('quiz_type').prefetch_related('answers').filter(is_active=True).order_by('-id')


# --- Savol qo'shish ---
class QuestionCreateView(SuperuserRequiredMixin, SuccessMessageMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = 'quiz/question_form.html'
    success_url = reverse_lazy('question_list')
    success_message = "Savol va javoblar muvaffaqiyatli qo'shildi!"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = AnswerFormSet(self.request.POST)
        else:
            context['formset'] = AnswerFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            correct_answers = [
                f for f in formset.forms
                if f.cleaned_data and not f.cleaned_data.get('DELETE', False) and f.cleaned_data.get('is_correct')
            ]

            if len(correct_answers) == 0:
                messages.error(self.request, "Kamida bitta to'g'ri javob bo'lishi kerak!")
                return self.form_invalid(form)
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            # Oxirgi tanlangan quiz_type ni saqlash
            quiz_type_id = form.cleaned_data['quiz_type'].id
            self.request.session['last_quiztype_id'] = quiz_type_id
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


# --- Savol tahrirlash ---
class QuestionUpdateView(SuperuserRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = 'quiz/question_form.html'
    success_url = reverse_lazy('question_list')
    success_message = "Savol muvaffaqiyatli yangilandi!"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = AnswerUpdateFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = AnswerUpdateFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            # Yangi tanlangan quiz_type ni saqlash
            quiz_type_id = form.cleaned_data['quiz_type'].id
            self.request.session['last_quiztype_id'] = quiz_type_id
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


# --- Savol o'chirish ---
class QuestionDeleteView(SuperuserRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Question
    template_name = 'quiz/question_confirm_delete.html'
    success_url = reverse_lazy('question_list')
    success_message = "Savol muvaffaqiyatli o‘chirildi!"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)