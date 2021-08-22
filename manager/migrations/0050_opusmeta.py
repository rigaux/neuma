# Generated by Django 2.2.13 on 2020-08-16 16:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0049_auto_20200618_1029'),
    ]

    operations = [
        migrations.CreateModel(
            name='OpusMeta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('meta_key', models.CharField(max_length=255)),
                ('meta_value', models.CharField(max_length=255)),
                ('opus', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.Opus')),
            ],
            options={
                'db_table': 'OpusMeta',
            },
        ),
    ]