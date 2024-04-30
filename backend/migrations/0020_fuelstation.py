# Generated by Django 5.0.1 on 2024-04-06 18:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0019_basketproduct_quantity'),
    ]

    operations = [
        migrations.CreateModel(
            name='FuelStation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('location', models.CharField(max_length=255)),
                ('fuel_type', models.CharField(max_length=50)),
                ('fuel_quantity', models.DecimalField(decimal_places=2, max_digits=10)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
