# Generated by Django 5.0.1 on 2024-04-17 17:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0027_alter_car_brand_alter_car_model'),
    ]

    operations = [
        migrations.RenameField(
            model_name='refuelinghistory',
            old_name='name',
            new_name='refueling_id',
        ),
        migrations.AddField(
            model_name='refuelinghistory',
            name='car',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='backend.car'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='refuelinghistory',
            name='fuel_column',
            field=models.ForeignKey(default=12, on_delete=django.db.models.deletion.CASCADE, to='backend.fuelcolumn'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='refuelinghistory',
            name='fuel_type',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='backend.fueltype'),
            preserve_default=False,
        ),
    ]
