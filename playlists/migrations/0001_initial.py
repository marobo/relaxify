# Generated by Django 5.2.2 on 2025-06-09 06:48

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Playlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('youtube_id', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
                ('thumbnail_url', models.URLField(blank=True, null=True)),
                ('duration', models.CharField(blank=True, max_length=20)),
                ('view_count', models.IntegerField(default=0)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Playlist',
                'verbose_name_plural': 'Playlists',
                'ordering': ['-created'],
            },
        ),
    ]
