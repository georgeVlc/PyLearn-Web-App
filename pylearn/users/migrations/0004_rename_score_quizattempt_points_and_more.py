# Generated by Django 5.1.3 on 2024-12-26 16:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_taskattempt'),
    ]

    operations = [
        migrations.RenameField(
            model_name='quizattempt',
            old_name='score',
            new_name='points',
        ),
        migrations.RenameField(
            model_name='taskattempt',
            old_name='score',
            new_name='points',
        ),
        migrations.AddField(
            model_name='taskattempt',
            name='accuracy',
            field=models.FloatField(default=0.0),
        ),
    ]