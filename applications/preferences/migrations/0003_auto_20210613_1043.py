# Generated by Django 3.1.5 on 2021-06-13 15:43

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('preferences', '0002_preferencesarea_filters_area'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreferencesFilterArea',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('filters_area', models.CharField(blank=True, max_length=50, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='preferences',
            name='search_value',
        ),
        migrations.RemoveField(
            model_name='preferencesarea',
            name='filters_area',
        ),
        migrations.CreateModel(
            name='PreferencesFilters',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('search_value', models.CharField(blank=True, max_length=50, null=True)),
                ('preferences_filter_area', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preferences_filter', to='preferences.preferencesfilterarea')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
