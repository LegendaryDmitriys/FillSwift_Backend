# Generated by Django 5.0.1 on 2024-03-08 18:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0009_remove_product_code_product_description_product_name'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Product',
        ),
    ]
