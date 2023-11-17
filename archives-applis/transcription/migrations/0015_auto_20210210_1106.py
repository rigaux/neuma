# Generated by Django 2.2.18 on 2021-02-10 11:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transcription', '0014_remove_grammarstate_grammar'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='grammarrule',
            name='type_weight',
        ),
        migrations.AddField(
            model_name='grammar',
            name='type_weight',
            field=models.CharField(choices=[('proba', 'Probability'), ('proba', 'Penalty')], default='proba', max_length=30),
        ),
    ]