# Generated by Django 5.1.4 on 2025-01-09 19:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Название')),
                ('url', models.URLField(blank=True, null=True, verbose_name='Ссылка')),
                ('state', models.BooleanField(default=True, verbose_name='статус получения заказов')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Магазин',
                'verbose_name_plural': 'Список магазинов',
                'ordering': ('-name',),
            },
        ),
    ]
