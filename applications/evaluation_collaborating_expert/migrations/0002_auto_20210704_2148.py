# Generated by Django 3.1.5 on 2021-07-05 02:48

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('learning_object_metadata', '0001_initial'),
        ('evaluation_collaborating_expert', '0001_initial'),
    ]

    operations = [
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
                ('evaluation_concept', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluation_automatic_evaluation', to='evaluation_collaborating_expert.evaluationconcept')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='evaluationquestion',
            name='interpreter_no',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='evaluationquestion',
            name='interpreter_partially',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='evaluationquestion',
            name='interpreter_yes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='evaluationquestion',
            name='value_importance',
            field=models.FloatField(blank=True, null=True),
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
    ]
