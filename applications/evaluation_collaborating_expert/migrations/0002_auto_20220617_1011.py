# Generated by Django 3.1.5 on 2022-06-17 15:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation_collaborating_expert', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluationquestion',
            name='relevance',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='evaluationquestion',
            name='weight',
            field=models.FloatField(blank=True, null=True),
        ),
    ]