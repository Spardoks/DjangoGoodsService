# Generated by Django 5.1.4 on 2025-01-09 21:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0005_productinfo'),
    ]

    operations = [
        migrations.CreateModel(
            name='Parameter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40, verbose_name='Название')),
            ],
            options={
                'verbose_name': 'Имя параметра',
                'verbose_name_plural': 'Список имен параметров',
                'ordering': ('-name',),
            },
        ),
    ]
