# Generated by Django 5.0.3 on 2025-02-25 08:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0020_rename_client_cart_buyer'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='total_price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
