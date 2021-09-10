# Generated by Django 3.1.5 on 2021-06-12 04:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('learning_object_metadata', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Interaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('liked', models.BooleanField(default=False)),
                ('viewed', models.BooleanField(default=False)),
                ('learning_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='oa_liked', to='learning_object_metadata.learningobjectmetadata')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_interacted', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
