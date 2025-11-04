# quiz/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Question, Answer, QuizType



class QuizTypeForm(forms.ModelForm):
    class Meta:
        model = QuizType
        fields = ['name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Quiz turi nomi'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Nomi',
            'is_active': 'Faol',
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['quiz_type', 'name', 'is_active']
        widgets = {
            'quiz_type': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'quiz_type': 'Quiz turi',
            'name': 'Savol matni',
            'is_active': 'Faol',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Oxirgi tanlangan quiz_type ni saqlash uchun
        self.fields['quiz_type'].queryset = QuizType.objects.filter(is_active=True)


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['name', 'is_correct', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Javob matni'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Javob',
            'is_correct': 'To‘g‘ri',
            'is_active': 'Faol',
        }

# Inline formset: 4 ta bo'sh javob + dinamik qo'shish
AnswerFormSet = inlineformset_factory(
    Question, Answer,
    form=AnswerForm,
    extra=4,          # 4 ta bo'sh maydon
    can_delete=True,  # o'chirish imkoniyati
    max_num=20        # maksimum 20 ta javob
)

AnswerUpdateFormSet = inlineformset_factory(
    Question, Answer,
    form=AnswerForm,
    extra=2,          # 0 ta bo'sh maydon
    can_delete=True,  # o'chirish imkoniyati
    max_num=20        # maksimum 20 ta javob
)






class UploadWordForm(forms.Form):
    quiz_type = forms.ModelChoiceField(
        queryset=QuizType.objects.filter(is_active=True),
        label="Test turi (Quiz nomi)",
        empty_label="Tanlang...",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    file = forms.FileField(label="Word faylni yuklang (.docx)")

