# Generated by Django 5.0.3 on 2025-02-25 08:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0019_alter_product_product_quantity'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cart',
            old_name='client',
            new_name='buyer',
        ),
    ]
