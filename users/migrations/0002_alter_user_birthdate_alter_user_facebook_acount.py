# Generated by Django 5.1.7 on 2025-04-06 22:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='Birthdate',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='facebook_acount',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
