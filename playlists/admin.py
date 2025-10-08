from django.contrib import admin
from .models import Playlist, PlaylistCollection, UserPlaylistCollection


@admin.register(PlaylistCollection)
class PlaylistCollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'platform', 'playlist_count', 'total_duration_formatted', 'is_active', 'created']
    list_filter = ['platform', 'is_active', 'created']
    search_fields = ['name', 'description']
    readonly_fields = ['created', 'updated', 'playlist_count', 'total_duration_formatted']
    fields = ['name', 'description', 'platform', 'youtube_playlist_id', 'thumbnail_url', 'is_active', 'created', 'updated']


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ['title', 'artist', 'collection', 'platform_source', 'duration', 'view_count', 'is_active', 'created']
    list_filter = ['platform_source', 'is_active', 'created', 'collection']
    search_fields = ['title', 'artist', 'album', 'youtube_id']
    readonly_fields = ['created', 'updated', 'youtube_url', 'embed_url']
    list_per_page = 50
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'artist', 'album', 'track_number', 'collection')
        }),
        ('YouTube Details', {
            'fields': ('youtube_id', 'platform_source', 'thumbnail_url', 'youtube_url', 'embed_url')
        }),
        ('Metadata', {
            'fields': ('description', 'duration', 'duration_seconds', 'view_count')
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created', 'updated')
        }),
    )


@admin.register(UserPlaylistCollection)
class UserPlaylistCollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'total_tracks', 'is_public', 'created']
    list_filter = ['is_public', 'created']
    search_fields = ['name', 'description']
    readonly_fields = ['created', 'updated', 'total_tracks']
    filter_horizontal = ['collections', 'tracks']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_public')
        }),
        ('Collections & Tracks', {
            'fields': ('collections', 'tracks')
        }),
        ('Metadata', {
            'fields': ('total_tracks', 'created', 'updated')
        }),
    )
