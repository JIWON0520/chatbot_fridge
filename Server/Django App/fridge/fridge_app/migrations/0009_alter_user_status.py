# Generated by Django 4.0.2 on 2022-04-29 15:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fridge_app', '0008_alter_item_idate_alter_user_cidate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='status',
            field=models.FloatField(default=0),
        ),
    ]