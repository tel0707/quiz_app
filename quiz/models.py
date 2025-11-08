from datetime import datetime
from django.db import models
from django.contrib.auth.models import User


# --- 1️⃣ Test turlari ---
class QuizType(models.Model):
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# --- 2️⃣ Savollar ---
class Question(models.Model):
    quiz_type = models.ForeignKey(QuizType, on_delete=models.CASCADE, related_name='questions')
    name = models.CharField(max_length=1000)
    is_active = models.BooleanField(default=True)
    is_multiple_choice = models.BooleanField(default=False)

    def __str__(self):
        return self.name




# --- 3️⃣ Javob variantlari ---
class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    name = models.CharField(max_length=1000)
    is_active = models.BooleanField(default=True)
    is_correct = models.BooleanField(default=False)


    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Javobni avval saqlaymiz
        # Bog'langan savolning multiple_choice ni yangilaymiz
        correct_count = Answer.objects.filter(question=self.question, is_correct=True).count()
        is_multi = correct_count > 1
        if self.question.is_multiple_choice != is_multi:
            self.question.is_multiple_choice = is_multi
            self.question.save(update_fields=['is_multiple_choice'])



# --- 4️⃣ Foydalanuvchi uchun yaratilgan test (har safar yangi test instance) ---
class GenerateQuiz(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes')
    quiz_type = models.ForeignKey(QuizType, on_delete=models.CASCADE, related_name='generated_quizzes')
    score = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(null=True, blank=True)
    numbers = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.numbers

    def save(self, *args, **kwargs):
        if not self.numbers:
            year = datetime.now().year
            last_quiz = GenerateQuiz.objects.filter(numbers__contains=f"Test-{year}-").order_by('-id').first()
            last_num = 0
            if last_quiz:
                try:
                    last_num = int(last_quiz.numbers.split('-')[-1])
                except ValueError:
                    pass
            next_num = str(last_num + 1).zfill(6)
            self.numbers = f"Test-{year}-{next_num}"
        super().save(*args, **kwargs)


# --- 5️⃣ Har bir testdagi savollar (ko‘p savollik test uchun oraliq model) ---
class GenerateQuizQuestion(models.Model):
    quiz = models.ForeignKey(GenerateQuiz, on_delete=models.CASCADE, related_name='questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='quiz_links')

    def __str__(self):
        return f"{self.quiz.numbers} - {self.question.name}"


# --- 6️⃣ Foydalanuvchining javoblari ---
class AnswerUsers(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers_given')
    generate_quiz = models.ForeignKey(GenerateQuiz, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='user_question_answers')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='chosen_by_users')

    class Meta:
        unique_together = ('user', 'generate_quiz', 'question', 'answer')

    def __str__(self):
        return f"{self.user.username} → {self.generate_quiz.numbers}"
