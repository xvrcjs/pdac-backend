# Generated by Django 4.2.16 on 2024-11-04 19:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0003_remove_policy_created_by_remove_policy_modified_by_and_more'),
        ('users', '0003_remove_account_policies_account_permissions'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Policy',
        ),
    ]
