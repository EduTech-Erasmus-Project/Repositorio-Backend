# Generated by Django 3.1.5 on 2022-06-16 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation_student', '0002_auto_20220616_1022'),
    ]

    operations = [
        migrations.AlterField(
            model_name='question',
            name='relevance',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
