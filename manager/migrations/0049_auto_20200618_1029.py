# Generated by Django 2.2.13 on 2020-06-18 10:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0048_auto_20200618_1025'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookmark',
            name='opus',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.Opus'),
        ),
        migrations.AlterField(
            model_name='bookmark',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]