# Generated by Django 3.2.5 on 2021-12-08 22:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0059_licence'),
    ]

    operations = [
        migrations.AlterField(
            model_name='licence',
            name='url',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
