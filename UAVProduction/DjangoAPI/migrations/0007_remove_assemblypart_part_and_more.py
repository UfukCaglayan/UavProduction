# Generated by Django 5.0.6 on 2024-12-14 13:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('DjangoAPI', '0006_alter_partproduction_production_time_assembly_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='assemblypart',
            name='part',
        ),
        migrations.AddField(
            model_name='assemblypart',
            name='part_production',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='DjangoAPI.partproduction'),
        ),
    ]