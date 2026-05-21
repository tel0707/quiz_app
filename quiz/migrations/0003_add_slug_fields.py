from django.db import migrations, models
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    QuizType = apps.get_model('quiz', 'QuizType')
    for obj in QuizType.objects.all():
        if not obj.slug:
            base = slugify(obj.name) or f"quiztype-{obj.pk}"
            slug, n = base, 1
            while QuizType.objects.filter(slug=slug).exclude(pk=obj.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            obj.slug = slug
            obj.save()

    Question = apps.get_model('quiz', 'Question')
    for obj in Question.objects.all():
        if not obj.slug:
            base = slugify(obj.name)[:80] or f"question-{obj.pk}"
            slug, n = base, 1
            while Question.objects.filter(slug=slug).exclude(pk=obj.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            obj.slug = slug
            obj.save()


class Migration(migrations.Migration):
    # atomic=False: har bir operatsiya alohida, biri xato bo'lsa boshqalari davom etadi
    atomic = False

    dependencies = [
        ('quiz', '0002_remove_answer_is_multiple_choice_and_more'),
    ]

    operations = [
        # 1. QuizType.slug ustunini qo'shish (IF NOT EXISTS — xavfsiz)
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    "ALTER TABLE quiz_quiztype ADD COLUMN IF NOT EXISTS slug VARCHAR(220) NOT NULL DEFAULT '';",
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='quiztype',
                    name='slug',
                    field=models.SlugField(max_length=220, blank=True, default=''),
                ),
            ],
        ),

        # 2. Question.slug ustunini qo'shish (IF NOT EXISTS — xavfsiz)
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    "ALTER TABLE quiz_question ADD COLUMN IF NOT EXISTS slug VARCHAR(100) NOT NULL DEFAULT '';",
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='question',
                    name='slug',
                    field=models.SlugField(max_length=100, blank=True, default=''),
                ),
            ],
        ),

        # 3. Mavjud yozuvlar uchun slug to'ldirish (bo'sh bo'lganlar uchun)
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),

        # 4. QuizType.slug — unique index (IF NOT EXISTS — xavfsiz)
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        DO $$ BEGIN
                            IF NOT EXISTS (
                                SELECT 1
                                FROM information_schema.table_constraints tc
                                JOIN information_schema.constraint_column_usage ccu
                                    ON tc.constraint_name = ccu.constraint_name
                                    AND tc.table_schema = ccu.table_schema
                                WHERE tc.table_schema = 'public'
                                  AND tc.table_name   = 'quiz_quiztype'
                                  AND tc.constraint_type = 'UNIQUE'
                                  AND ccu.column_name = 'slug'
                            ) THEN
                                ALTER TABLE quiz_quiztype ADD UNIQUE (slug);
                            END IF;

                            IF NOT EXISTS (
                                SELECT 1 FROM pg_indexes
                                WHERE tablename = 'quiz_quiztype'
                                  AND indexdef LIKE '%varchar_pattern_ops%'
                                  AND indexdef LIKE '%slug%'
                            ) THEN
                                CREATE INDEX ON quiz_quiztype (slug varchar_pattern_ops);
                            END IF;
                        END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name='quiztype',
                    name='slug',
                    field=models.SlugField(max_length=220, unique=True),
                ),
            ],
        ),

        # 5. Question.slug — unique index (IF NOT EXISTS — xavfsiz)
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        DO $$ BEGIN
                            IF NOT EXISTS (
                                SELECT 1
                                FROM information_schema.table_constraints tc
                                JOIN information_schema.constraint_column_usage ccu
                                    ON tc.constraint_name = ccu.constraint_name
                                    AND tc.table_schema = ccu.table_schema
                                WHERE tc.table_schema = 'public'
                                  AND tc.table_name   = 'quiz_question'
                                  AND tc.constraint_type = 'UNIQUE'
                                  AND ccu.column_name = 'slug'
                            ) THEN
                                ALTER TABLE quiz_question ADD UNIQUE (slug);
                            END IF;

                            IF NOT EXISTS (
                                SELECT 1 FROM pg_indexes
                                WHERE tablename = 'quiz_question'
                                  AND indexdef LIKE '%varchar_pattern_ops%'
                                  AND indexdef LIKE '%slug%'
                            ) THEN
                                CREATE INDEX ON quiz_question (slug varchar_pattern_ops);
                            END IF;
                        END $$;
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name='question',
                    name='slug',
                    field=models.SlugField(max_length=100, unique=True),
                ),
            ],
        ),
    ]
