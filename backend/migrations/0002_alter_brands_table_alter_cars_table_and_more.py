# Generated by Django 5.0.1 on 2024-01-19 17:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='brands',
            table='brands',
        ),
        migrations.AlterModelTable(
            name='cars',
            table='cars',
        ),
        migrations.AlterModelTable(
            name='customers',
            table='customers',
        ),
        migrations.AlterModelTable(
            name='fuelcolumns',
            table='fuelcolumns',
        ),
        migrations.AlterModelTable(
            name='fueling',
            table='fueling',
        ),
        migrations.AlterModelTable(
            name='fueltypes',
            table='fueltypes',
        ),
        migrations.AlterModelTable(
            name='products',
            table='products',
        ),
        migrations.AlterModelTable(
            name='storepurchases',
            table='storepurchases',
        ),
    ]
