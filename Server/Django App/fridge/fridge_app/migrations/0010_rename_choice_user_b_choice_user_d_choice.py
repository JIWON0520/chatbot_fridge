# Generated by Django 4.0.2 on 2022-04-30 05:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fridge_app', '0009_alter_user_status'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='choice',
            new_name='b_choice',
        ),
        migrations.AddField(
            model_name='user',
            name='d_choice',
            field=models.CharField(default='none', max_length=10),
        ),
    ]
