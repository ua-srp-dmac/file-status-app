# Generated by Django 3.1.1 on 2020-09-09 01:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CyVerseAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('api_token', models.TextField(blank=True, max_length=100)),
                ('api_token_expiration', models.DateTimeField(blank=True, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cyverse_account', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'CyVerse Account',
                'ordering': ('-pk',),
            },
        ),
    ]
