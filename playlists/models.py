from django.db import models
from django.utils import timezone


class Playlist(models.Model):
    """
    Model representing a YouTube playlist for relaxing music
    """
    title = models.CharField(max_length=200)
    youtube_id = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    thumbnail_url = models.URLField(blank=True, null=True)
    duration = models.CharField(max_length=20, blank=True)  # Duration in readable format
    view_count = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created']
        verbose_name = 'Playlist'
        verbose_name_plural = 'Playlists'

    def __str__(self):
        return self.title

    @property
    def youtube_url(self):
        """Returns the full YouTube URL for this playlist"""
        return f"https://www.youtube.com/watch?v={self.youtube_id}"

    @property
    def embed_url(self):
        """Returns the YouTube embed URL for this playlist"""
        return f"https://www.youtube.com/embed/{self.youtube_id}"
