<<<<<<< HEAD
# Generated by Django 3.1.5 on 2022-05-19 14:40
=======
# Generated by Django 3.1.5 on 2022-05-16 14:24
>>>>>>> a02792c025cc59d587981680562af0fece3dd9af

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
<<<<<<< HEAD
        ('learning_object_metadata', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
=======
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('learning_object_metadata', '0001_initial'),
>>>>>>> a02792c025cc59d587981680562af0fece3dd9af
    ]

    operations = [
        migrations.CreateModel(
            name='EvaluationGuidelineQualification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('average_guideline', models.FloatField(default=0.0)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Guideline',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('guideline', models.CharField(max_length=1000, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Principle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('principle', models.CharField(max_length=500, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StudentEvaluation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('observation', models.TextField(blank=True, null=True)),
                ('rating', models.FloatField(default=0.0)),
                ('learning_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_learning_objects', to='learning_object_metadata.learningobjectmetadata')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_evaluation', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('question', models.CharField(max_length=1000, unique=True)),
                ('description', models.TextField()),
                ('metadata', models.TextField()),
                ('interpreter_st_yes', models.TextField(blank=True, null=True)),
                ('interpreter_st_no', models.TextField(blank=True, null=True)),
                ('interpreter_st_partially', models.TextField(blank=True, null=True)),
                ('interpreter_st_not_apply', models.TextField(blank=True, null=True)),
                ('value_st_importance', models.FloatField(blank=True, null=True)),
                ('guideline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='evaluation_student.guideline')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='guideline',
            name='principle',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='guidelines', to='evaluation_student.principle'),
        ),
        migrations.CreateModel(
            name='EvaluationQuestionQualification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('qualification', models.FloatField()),
                ('evaluation_question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluation_questions', to='evaluation_student.question')),
                ('guideline_evaluations', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='guideline_evaluations', to='evaluation_student.evaluationguidelinequalification')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EvaluationPrincipleQualification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('average_principle', models.FloatField(default=0.0)),
                ('evaluation_principle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluation_principles', to='evaluation_student.principle')),
                ('evaluation_student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluation_students', to='evaluation_student.studentevaluation')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='evaluationguidelinequalification',
            name='guideline_pr',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='guideline_pr', to='evaluation_student.guideline'),
        ),
        migrations.AddField(
            model_name='evaluationguidelinequalification',
            name='principle_gl',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='principle_gl', to='evaluation_student.evaluationprinciplequalification'),
        ),
    ]
