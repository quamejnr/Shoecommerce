# Generated by Django 3.1.4 on 2020-12-28 12:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0014_auto_20201225_1223'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderitem',
            name='order',
        ),
        migrations.AddField(
            model_name='orderitem',
            name='order',
            field=models.ManyToManyField(blank=True, null=True, to='shop.Order'),
        ),
    ]
