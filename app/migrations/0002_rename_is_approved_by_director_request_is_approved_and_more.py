# Generated by Django 5.0.3 on 2024-08-16 15:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='request',
            old_name='is_approved_by_director',
            new_name='is_approved',
        ),
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(blank=True, choices=[('ICT Director', 'ict_director'), ('Team Leader', 'team_leader'), ('Staff', 'staff'), ('Client', 'client')], default='Client', max_length=100, verbose_name='Role'),
        ),
    ]
