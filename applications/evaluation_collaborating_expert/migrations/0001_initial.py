# Generated by Django 3.1.5 on 2021-11-09 03:33

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('learning_object_metadata', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EvaluationCollaboratingExpert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('rating', models.FloatField()),
                ('observation', models.TextField(blank=True, null=True)),
                ('collaborating_expert', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_evaluation', to=settings.AUTH_USER_MODEL)),
                ('learning_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='learning_objects', to='learning_object_metadata.learningobjectmetadata')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EvaluationConcept',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('concept', models.CharField(max_length=500, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EvaluationConceptQualification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('average', models.FloatField(default=0.0)),
                ('evaluation_collaborating_expert', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='concept_evaluations', to='evaluation_collaborating_expert.evaluationcollaboratingexpert')),
                ('evaluation_concept', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluation_concept', to='evaluation_collaborating_expert.evaluationconcept')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EvaluationMetadata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('schema', models.TextField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('value_importance_schema', models.FloatField(blank=True, null=True)),
                ('code', models.CharField(max_length=10, unique=True)),
                ('evaluation_concept', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schemas', to='evaluation_collaborating_expert.evaluationconcept')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EvaluationQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('question', models.TextField(unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('schema', models.TextField(blank=True, null=True)),
                ('interpreter_yes', models.TextField(blank=True, null=True)),
                ('interpreter_no', models.TextField(blank=True, null=True)),
                ('interpreter_partially', models.TextField(blank=True, null=True)),
                ('value_importance', models.FloatField(blank=True, null=True)),
                ('code', models.CharField(max_length=10, unique=True)),
                ('evaluation_concept', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='evaluation_collaborating_expert.evaluationconcept')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MetadataAutomaticEvaluation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('rating_schema', models.FloatField()),
                ('learning_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='metadata_learning_objects', to='learning_object_metadata.learningobjectmetadata')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MetadataQualificationConcept',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('average_schema', models.FloatField(default=0.0)),
                ('evaluation_automatic_evaluation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='metadata_concept_evaluations', to='evaluation_collaborating_expert.metadataautomaticevaluation')),
                ('evaluation_concept', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluation_automatic_evaluations', to='evaluation_collaborating_expert.evaluationconcept')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MetadataSchemaQualification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('qualification', models.FloatField()),
                ('evaluation_metadata', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='metadata_evaluations', to='evaluation_collaborating_expert.metadataqualificationconcept')),
                ('evaluation_schema', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluation_schemas', to='evaluation_collaborating_expert.evaluationmetadata')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EvaluationQuestionsQualification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('qualification', models.FloatField()),
                ('concept_evaluations', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='question_evaluations', to='evaluation_collaborating_expert.evaluationconceptqualification')),
                ('evaluation_question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluation_questions', to='evaluation_collaborating_expert.evaluationquestion')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
