# Generated by Django 3.1.4 on 2020-12-18 13:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0008_auto_20201218_0110'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='transaction',
            new_name='transaction_id',
        ),
    ]
