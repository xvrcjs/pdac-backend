# Generated by Django 4.2.20 on 2025-04-27 16:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0003_standardsandprotocols'),
        ('users', '0008_account_support_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='omic',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='administration.omic', verbose_name='Omic'),
        ),
    ]
