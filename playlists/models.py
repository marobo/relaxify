from django.db import models
from django.utils import timezone


class PlaylistCollection(models.Model):
    """
    Model representing a collection of related playlists (from YouTube or YouTube Music)
    """
    PLATFORM_CHOICES = [
        ('youtube', 'YouTube'),
        ('youtube_music', 'YouTube Music'),
        ('mixed', 'Mixed')
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='youtube')
    youtube_playlist_id = models.CharField(max_length=50, blank=True, null=True)  # For actual YT playlists
    thumbnail_url = models.URLField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created']
        verbose_name = 'Playlist Collection'
        verbose_name_plural = 'Playlist Collections'
    
    def __str__(self):
        return f"{self.name} ({self.get_platform_display()})"
    
    @property
    def playlist_count(self):
        return self.playlists.filter(is_active=True).count()
    
    @property
    def total_duration_seconds(self):
        total = 0
        for playlist in self.playlists.filter(is_active=True):
            if playlist.duration_seconds:
                total += playlist.duration_seconds
        return total
    
    @property
    def total_duration_formatted(self):
        seconds = self.total_duration_seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"


class Playlist(models.Model):
    """
    Model representing a YouTube video/track for relaxing music
    """
    title = models.CharField(max_length=200)
    youtube_id = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    thumbnail_url = models.URLField(blank=True, null=True)
    duration = models.CharField(max_length=20, blank=True)  # Duration in readable format
    duration_seconds = models.IntegerField(blank=True, null=True)  # Duration in seconds for calculations
    view_count = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # New fields for playlist integration
    collection = models.ForeignKey(PlaylistCollection, on_delete=models.CASCADE, related_name='playlists', blank=True, null=True)
    artist = models.CharField(max_length=200, blank=True)
    album = models.CharField(max_length=200, blank=True)
    track_number = models.IntegerField(blank=True, null=True)
    platform_source = models.CharField(max_length=20, choices=PlaylistCollection.PLATFORM_CHOICES, default='youtube')

    class Meta:
        ordering = ['-created']
        verbose_name = 'Track'
        verbose_name_plural = 'Tracks'

    def __str__(self):
        return self.title

    @property
    def youtube_url(self):
        """Returns the full YouTube URL for this track"""
        return f"https://www.youtube.com/watch?v={self.youtube_id}"

    @property
    def embed_url(self):
        """Returns the YouTube embed URL for this track"""
        return f"https://www.youtube.com/embed/{self.youtube_id}"
    
    @property
    def youtube_music_url(self):
        """Returns the YouTube Music URL for this track"""
        return f"https://music.youtube.com/watch?v={self.youtube_id}"


class UserPlaylistCollection(models.Model):
    """
    Model for user-created playlist collections (combining multiple playlists)
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    collections = models.ManyToManyField(PlaylistCollection, related_name='user_collections')
    tracks = models.ManyToManyField(Playlist, related_name='user_collections', blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created']
        verbose_name = 'User Playlist Collection'
        verbose_name_plural = 'User Playlist Collections'
    
    def __str__(self):
        return self.name
    
    @property
    def total_tracks(self):
        direct_tracks = self.tracks.filter(is_active=True).count()
        collection_tracks = sum(collection.playlist_count for collection in self.collections.filter(is_active=True))
        return direct_tracks + collection_tracks
