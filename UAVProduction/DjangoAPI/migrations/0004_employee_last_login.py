# Generated by Django 5.0.6 on 2024-12-10 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('DjangoAPI', '0003_alter_employee_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='last_login',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]