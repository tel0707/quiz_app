# quiz/views.py
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Case, When
from .forms import QuizTypeForm, QuestionForm, AnswerFormSet, AnswerUpdateFormSet, UploadWordForm
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from docx import Document
import re
import random, json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from django.db import transaction
from django.utils import timezone
from .models import QuizType, Question, Answer, GenerateQuiz, AnswerUsers, GenerateQuizQuestion


# --- Superuser tekshiruvi ---
class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "Bu amalni faqat administrator bajarishi mumkin.")
        return redirect('quiztype_list')


# --- Ro'yxat (hamma ko'ra oladi) ---
class QuizTypeListView(ListView):
    model = QuizType
    template_name = 'quiz/quiztype_list.html'
    context_object_name = 'quiztypes'
    paginate_by = 10

    def get_queryset(self):
        return QuizType.objects.filter(is_active=True).order_by('-id')


# --- Yaratish (faqat superuser) ---
class QuizTypeCreateView(SuperuserRequiredMixin, SuccessMessageMixin, CreateView):
    model = QuizType
    form_class = QuizTypeForm
    template_name = 'quiz/quiztype_form.html'
    success_url = reverse_lazy('quiztype_list')
    success_message = "Quiz turi muvaffaqiyatli qo'shildi!"


# --- Tahrirlash (faqat superuser) ---
class QuizTypeUpdateView(SuperuserRequiredMixin, SuccessMessageMixin, UpdateView):
    model = QuizType
    form_class = QuizTypeForm
    template_name = 'quiz/quiztype_form.html'
    success_url = reverse_lazy('quiztype_list')
    success_message = "Quiz turi muvaffaqiyatli yangilandi!"


# --- O'chirish (faqat superuser) ---
class QuizTypeDeleteView(SuperuserRequiredMixin, SuccessMessageMixin, DeleteView):
    model = QuizType
    template_name = 'quiz/quiztype_confirm_delete.html'
    success_url = reverse_lazy('quiztype_list')
    success_message = "Quiz turi muvaffaqiyatli o'chirildi!"

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


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
    success_message = "Savol muvaffaqiyatli o'chirildi!"

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)


@login_required
def upload_quiz_from_word(request):
    if not request.user.is_superuser:
        messages.error(request, "Bu amalni faqat administrator bajarishi mumkin.")
        return redirect('quiztype_list')

    if request.method == "POST":
        form = UploadWordForm(request.POST, request.FILES)
        if form.is_valid():
            quiz_type = form.cleaned_data['quiz_type']
            file = request.FILES['file']

            try:
                doc = Document(file)
            except Exception as e:
                messages.error(request, f"❌ Word faylni o'qib bo'lmadi: {e}")
                return redirect("upload_quiz_from_word")

            lines = []
            for p in doc.paragraphs:
                t = p.text.strip()
                if t:
                    lines.append(t.replace("\xa0", " "))

            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        if cell_text:
                            lines.append(cell_text.replace("\xa0", " "))

            if not lines:
                messages.error(request, "❌ Fayldan hech qanday matn o'qilmadi.")
                return redirect("upload_quiz_from_word")

            question_blocks = []
            current_q = None
            current_answers = []
            q_pattern = re.compile(r'^\s*(\d+)\.\s*(.*)')

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                m = q_pattern.match(line)
                if m:
                    if current_q is not None:
                        question_blocks.append((current_q, current_answers))
                    num = m.group(1)
                    rest = m.group(2).strip()
                    if not rest:
                        rest = line
                    current_q = f"{num}. {rest}"
                    current_answers = []
                else:
                    current_answers.append(line)

            if current_q is not None:
                question_blocks.append((current_q, current_answers))

            if not question_blocks:
                messages.error(request, "❌ Faylda savollar topilmadi. Iltimos formatni tekshiring (1. Savol ...).")
                return redirect("upload_quiz_from_word")

            problems = []
            valid_blocks = []
            for q_text, answers in question_blocks:
                if not answers:
                    problems.append(f"'{q_text}' uchun javob topilmadi")
                else:
                    valid_blocks.append((q_text, answers))

            with transaction.atomic():
                created_questions = Question.objects.bulk_create([
                    Question(quiz_type=quiz_type, name=q_text)
                    for q_text, _ in valid_blocks
                ])

                # bulk_create does not call save(), so slugs must be generated manually
                existing_slugs = set(Question.objects.values_list('slug', flat=True))
                slugs_to_assign = []
                for q in created_questions:
                    base = slugify(q.name)[:80] or f"question-{q.pk or random.randint(10000,99999)}"
                    slug, n = base, 1
                    while slug in existing_slugs:
                        slug = f"{base}-{n}"
                        n += 1
                    existing_slugs.add(slug)
                    q.slug = slug
                    slugs_to_assign.append(q)
                Question.objects.bulk_update(slugs_to_assign, ['slug'])

                answers_to_create = []
                questions_to_update = []
                for question, (_, answers) in zip(created_questions, valid_blocks):
                    correct_count = 0
                    for ans_line in answers:
                        is_correct = False
                        text = ans_line
                        if text.startswith("*"):
                            is_correct = True
                            text = text[1:].strip()
                        elif "*" in text:
                            is_correct = True
                            text = text.replace("*", "").strip()
                        text = text.strip()
                        if not text:
                            continue
                        answers_to_create.append(Answer(question=question, name=text, is_correct=is_correct))
                        if is_correct:
                            correct_count += 1
                    if correct_count > 1:
                        question.is_multiple_choice = True
                        questions_to_update.append(question)

                Answer.objects.bulk_create(answers_to_create)
                if questions_to_update:
                    Question.objects.bulk_update(questions_to_update, ['is_multiple_choice'])

            msg = f"✅ {len(created_questions)} ta savol '{quiz_type.name}' turiga muvaffaqiyatli yuklandi."
            if problems:
                msg += " Ba'zi bloklarda muammo: " + "; ".join(problems[:5])
            messages.success(request, msg)
            return redirect("upload_quiz_from_word")

        else:
            messages.error(request, "❌ Forma to'ldirishda xatolik bor.")
            return redirect("upload_quiz_from_word")

    else:
        form = UploadWordForm()

    return render(request, "quiz/upload_quiz.html", {"form": form})


# 🔹 TESTNI BOSHLASH
@login_required
def generate_quiz(request, slug):
    n = int(request.GET.get("count", 10))
    quiz_type = get_object_or_404(QuizType, slug=slug)

    question_ids = list(
        Question.objects.filter(is_active=True, quiz_type_id=pk)
        .values_list('id', flat=True)
    )
    if not question_ids:
        messages.error(request, f"❌ '{quiz_type.name}' uchun faol savollar yo'q.")
        return redirect('quiztype_list')

    n = min(n, len(question_ids))
    selected_q_ids = random.sample(question_ids, n)

    with transaction.atomic():
        quiz = GenerateQuiz.objects.create(
            user=request.user,
            quiz_type=quiz_type
        )

        request.session['quiz_id'] = quiz.id
        request.session['selected_q_ids'] = selected_q_ids
        request.session['quiz_start_time'] = timezone.now().isoformat()
        request.session['answer_orders'] = {}
        request.session.modified = True

        GenerateQuizQuestion.objects.bulk_create([
            GenerateQuizQuestion(quiz=quiz, question_id=qid)
            for qid in selected_q_ids
        ])

    return redirect('quiz_page', quiz_slug=quiz.numbers, page=1)


# 🔹 SAVOLLARNI KO'RISH (har biri alohida sahifada)
@login_required
def quiz_page(request, quiz_slug, page):
    quiz = get_object_or_404(GenerateQuiz, numbers=quiz_slug, user=request.user)

    if quiz.finished:
        messages.info(request, "Bu test allaqachon yakunlangan.")
        return redirect('quiztype_list')

    selected_q_ids = request.session.get('selected_q_ids', [])

    questions = Question.objects.filter(id__in=selected_q_ids, is_active=True).prefetch_related(
        Prefetch('answers', queryset=Answer.objects.filter(is_active=True))
    )

    if selected_q_ids:
        preserved_order = Case(*[When(id=pk, then=pos) for pos, pk in enumerate(selected_q_ids)])
        questions = questions.order_by(preserved_order)

    paginator = Paginator(questions, 1)
    page_obj = paginator.get_page(page)
    question = page_obj.object_list[0] if page_obj else None

    answered_question_ids = set(AnswerUsers.objects.filter(
        user=request.user,
        generate_quiz=quiz
    ).values_list('question_id', flat=True))

    answered_pages = [idx for idx, q in enumerate(questions, 1) if q.id in answered_question_ids]

    # Javoblar tartibini sessiyada saqlash (har savol uchun bir marta aralashtiriladi)
    answer_orders = request.session.get('answer_orders', {})
    shuffled_answers = []
    selected_answer_id = None

    if question:
        q_key = str(question.id)
        all_answers = list(question.answers.all())

        if q_key not in answer_orders:
            random.shuffle(all_answers)
            answer_orders[q_key] = [a.id for a in all_answers]
            request.session['answer_orders'] = answer_orders
            request.session.modified = True
        else:
            order = answer_orders[q_key]
            answers_dict = {a.id: a for a in all_answers}
            all_answers = [answers_dict[aid] for aid in order if aid in answers_dict]

        shuffled_answers = all_answers

        user_answer = AnswerUsers.objects.filter(
            user=request.user,
            generate_quiz=quiz,
            question=question
        ).first()
        selected_answer_id = user_answer.answer_id if user_answer else None

    context = {
        'quiz_type': quiz.quiz_type,
        'quiz': quiz,
        'question': question,
        'paginator': paginator,
        'page_obj': page_obj,
        'answered_questions': answered_pages,
        'total_minutes': len(selected_q_ids),
        'shuffled_answers': shuffled_answers,
        'selected_answer_id': selected_answer_id,
    }
    response = render(request, 'quiz/quiz_page.html', context)
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response


# 🔹 AJAX ORQALI JAVOBNI SAQLASH
@login_required
def save_answer(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            q_id = int(data.get('question_id'))
            a_id = int(data.get('answer_id'))
            quiz_id = request.session.get('quiz_id')

            if not quiz_id:
                return JsonResponse({"success": False, "error": "Sessiya yo'qolgan"}, status=400)

            quiz = get_object_or_404(GenerateQuiz, id=quiz_id, user=request.user)

            if quiz.finished:
                return JsonResponse({"success": False, "error": "Test allaqachon yakunlangan"}, status=400)

            question = get_object_or_404(Question, id=q_id)
            answer = get_object_or_404(Answer, id=a_id, question=question)

            if not GenerateQuizQuestion.objects.filter(quiz=quiz, question=question).exists():
                return JsonResponse({"success": False, "error": "Savol bu testga tegishli emas"}, status=400)

            AnswerUsers.objects.filter(
                user=request.user,
                generate_quiz=quiz,
                question=question
            ).delete()

            AnswerUsers.objects.create(
                user=request.user,
                generate_quiz=quiz,
                question=question,
                answer=answer
            )

            selected_q_ids = request.session.get('selected_q_ids', [])
            answered = set(
                AnswerUsers.objects.filter(user=request.user, generate_quiz=quiz).values_list('question_id', flat=True)
            )
            answered_pages = [idx for idx, qid in enumerate(selected_q_ids, 1) if qid in answered]
            return JsonResponse({
                "success": True,
                "answered_questions": answered_pages
            })

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False}, status=400)


# 🔹 TESTNI TUGATISH
@login_required
def finish_quiz(request):
    quiz_id = request.session.get('quiz_id')
    if not quiz_id:
        return redirect('quiztype_list')

    quiz = get_object_or_404(GenerateQuiz, id=quiz_id, user=request.user)
    selected_q_ids = request.session.get('selected_q_ids', [])
    total_questions = len(selected_q_ids)

    answers = AnswerUsers.objects.filter(user=request.user, generate_quiz=quiz).select_related('answer')
    correct = sum(1 for ans in answers if ans.answer.is_correct)

    quiz.score = int((correct / total_questions) * 100) if total_questions > 0 else 0
    quiz.finished = timezone.now()
    quiz.save()

    for key in ['quiz_id', 'selected_q_ids', 'quiz_start_time', 'answer_orders']:
        request.session.pop(key, None)

    response = render(request, 'quiz/quiz_result.html', {
        'quiz': quiz,
        'total': total_questions,
        'answered': answers.count(),
        'correct': correct,
        'percent': quiz.score,
    })
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    return response


# 🔹 LOGIN sahifasi
def user_login(request):
    if request.user.is_authenticated:
        return redirect('quiztype_list')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        username = username.lower()
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Xush kelibsiz, {user.username}!")
            return redirect('quiztype_list')
        else:
            messages.error(request, "Login yoki parol noto'g'ri!")

    return render(request, 'quiz/login.html')


# 🔹 LOGOUT
def user_logout(request):
    logout(request)
    messages.info(request, "Tizimdan chiqdingiz.")
    return redirect('login')


# 🔹 SIGNUP (ro'yxatdan o'tish)
def user_signup(request):
    if request.user.is_authenticated:
        return redirect('quiztype_list')

    if request.method == 'POST':
        input_username = request.POST.get('username')
        first_name = request.POST.get('firstname')
        last_name = request.POST.get('lastname')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        if chek_user(input_username):
            username = input_username.lower()
        else:
            messages.error(request, "Foydalanuvchi nomi 3–20 belgi oralig'ida, faqat lotin harflari, raqamlar va '_' belgilardan iborat bo'lishi kerak!")
            return redirect('signup')
        if password1 != password2:
            messages.error(request, "Parollar bir xil emas!")
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Bu foydalanuvchi nomi allaqachon mavjud.")
            return redirect('signup')

        user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name, email=email, password=password1)
        login(request, user)
        messages.success(request, "Muvaffaqiyatli ro'yxatdan o'tdingiz!")
        return redirect('quiztype_list')

    return render(request, 'quiz/signup.html')


def chek_user(username: str) -> bool:
    if not isinstance(username, str):
        return False
    if len(username) < 3 or len(username) > 20:
        return False
    pattern = r'^[a-zA-Z0-9_]+$'
    return bool(re.match(pattern, username))


@login_required
def all_quiz_results(request):
    if not request.user.is_superuser:
        messages.error(request, "Bu sahifaga faqat administrator kirishi mumkin.")
        return redirect('quiztype_list')

    qs = (
        GenerateQuiz.objects
        .filter(finished__isnull=False)
        .select_related('user', 'quiz_type')
        .order_by('-finished')
    )

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(user__username__icontains=search) | qs.filter(user__first_name__icontains=search) | qs.filter(user__last_name__icontains=search)
        qs = qs.order_by('-finished')

    quiz_type_id = request.GET.get('quiz_type', '')
    if quiz_type_id:
        qs = qs.filter(quiz_type_id=quiz_type_id)

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    quiz_types = QuizType.objects.filter(is_active=True).order_by('name')

    return render(request, 'quiz/all_results.html', {
        'page_obj': page_obj,
        'search': search,
        'quiz_types': quiz_types,
        'selected_quiz_type': quiz_type_id,
    })


@login_required
def export_results_excel(request):
    if not request.user.is_superuser:
        messages.error(request, "Bu amalni faqat administrator bajarishi mumkin.")
        return redirect('quiztype_list')

    qs = (
        GenerateQuiz.objects
        .filter(finished__isnull=False)
        .select_related('user', 'quiz_type')
        .order_by('-finished')
    )

    search = request.GET.get('q', '').strip()
    if search:
        qs = (
            qs.filter(user__username__icontains=search) |
            qs.filter(user__first_name__icontains=search) |
            qs.filter(user__last_name__icontains=search)
        ).order_by('-finished')

    quiz_type_id = request.GET.get('quiz_type', '')
    if quiz_type_id:
        qs = qs.filter(quiz_type_id=quiz_type_id)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Natijalar"

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(fill_type="solid", fgColor="2563EB")
    center = Alignment(horizontal="center", vertical="center")

    headers = ["#", "To'liq ism", "Username", "Test raqami", "Test turi", "Natija (%)", "Yakunlangan vaqt"]
    col_widths = [5, 25, 18, 20, 25, 14, 22]

    for col_num, (header, width) in enumerate(zip(headers, col_widths), 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        ws.column_dimensions[cell.column_letter].width = width

    ws.row_dimensions[1].height = 20

    for row_num, quiz in enumerate(qs, 1):
        full_name = quiz.user.get_full_name() or quiz.user.username
        finished_str = quiz.finished.strftime("%d.%m.%Y %H:%M") if quiz.finished else ""
        row = [
            row_num,
            full_name,
            quiz.user.username,
            quiz.numbers,
            quiz.quiz_type.name,
            quiz.score,
            finished_str,
        ]
        for col_num, value in enumerate(row, 1):
            cell = ws.cell(row=row_num + 1, column=col_num, value=value)
            if col_num in (1, 6):
                cell.alignment = center

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="quiz_natijalar.xlsx"'
    wb.save(response)
    return response


@login_required
def result_users(request, quiz_slug):
    if request.user.is_superuser:
        quiz = get_object_or_404(GenerateQuiz, numbers=quiz_slug)
    else:
        quiz = get_object_or_404(GenerateQuiz, numbers=quiz_slug, user=request.user)

    quiz_user = quiz.user

    my_tests = (
        AnswerUsers.objects
        .filter(user=quiz_user, generate_quiz=quiz)
        .select_related('question', 'answer')
        .order_by('-id')
    )

    question_ids = my_tests.values_list('question_id', flat=True)
    answer = Answer.objects.filter(question_id__in=question_ids)

    context = {
        'user': quiz_user,
        'my_tests': my_tests,
        'answer': answer,
    }
    return render(request, 'quiz/result_users.html', context)
