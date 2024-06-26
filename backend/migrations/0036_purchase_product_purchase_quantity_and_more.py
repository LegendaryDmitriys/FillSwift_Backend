# Generated by Django 5.0.1 on 2024-04-28 11:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0035_purchase_total_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='product',
            field=models.ForeignKey(default=12, on_delete=django.db.models.deletion.CASCADE, to='backend.product'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='purchase',
            name='quantity',
            field=models.IntegerField(default=12),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='PurchaseItem',
        ),
    ]
