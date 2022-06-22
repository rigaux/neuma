# Generated by Django 3.1 on 2022-06-01 13:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0069_auto_20220601_1259'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='selector_conforms_to',
            field=models.CharField(choices=[('http://tools.ietf.org/rfc/rfc3023', 'An XPointer expression'), ('http://www.w3.org/TR/media-frags/', 'A segment in a multimedia document')], default='http://tools.ietf.org/rfc/rfc3023', max_length=100),
        ),
        migrations.AlterField(
            model_name='resource',
            name='selector_type',
            field=models.CharField(default='None', max_length=100),
        ),
    ]