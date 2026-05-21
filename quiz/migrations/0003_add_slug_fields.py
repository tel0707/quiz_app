from django.db import migrations, models
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    QuizType = apps.get_model('quiz', 'QuizType')
    for obj in QuizType.objects.all():
        base = slugify(obj.name) or f"quiztype-{obj.pk}"
        slug, n = base, 1
        while QuizType.objects.filter(slug=slug).exclude(pk=obj.pk).exists():
            slug = f"{base}-{n}"
            n += 1
        obj.slug = slug
        obj.save()

    Question = apps.get_model('quiz', 'Question')
    for obj in Question.objects.all():
        base = slugify(obj.name)[:80] or f"question-{obj.pk}"
        slug, n = base, 1
        while Question.objects.filter(slug=slug).exclude(pk=obj.pk).exists():
            slug = f"{base}-{n}"
            n += 1
        obj.slug = slug
        obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0002_remove_answer_is_multiple_choice_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='quiztype',
            name='slug',
            field=models.SlugField(max_length=220, blank=True, default=''),
        ),
        migrations.AddField(
            model_name='question',
            name='slug',
            field=models.SlugField(max_length=100, blank=True, default=''),
        ),
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='quiztype',
            name='slug',
            field=models.SlugField(max_length=220, unique=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='slug',
            field=models.SlugField(max_length=100, unique=True),
        ),
    ]
