# Generated by Django 4.2 on 2024-11-20 05:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Core', '0002_remove_cntry_mstr_country_code_cntry_mstr_timezone'),
        ('UserManagement', '0004_delete_selectedessuser'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='country',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='Core.cntry_mstr'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='company',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
    ]