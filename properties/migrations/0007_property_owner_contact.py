# Generated by Django 5.2 on 2025-05-10 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0006_property_has_balcony_property_has_elevator_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='owner_contact',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='اطلاعات تماس مالک'),
        ),
    ]
