# Generated by Django 5.2 on 2025-05-07 12:40

import django_jalali.db.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='created_at',
            field=django_jalali.db.models.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت'),
        ),
        migrations.AlterField(
            model_name='property',
            name='updated_at',
            field=django_jalali.db.models.jDateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی'),
        ),
    ]
