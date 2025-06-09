from django.contrib import admin
from .models import Playlist


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('title', 'youtube_id', 'view_count', 'is_active', 'created', 'updated')
    list_filter = ('is_active', 'created', 'updated')
    search_fields = ('title', 'youtube_id', 'description')
    readonly_fields = ('youtube_url', 'embed_url', 'created', 'updated')
    list_editable = ('is_active',)
    ordering = ('-created',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'youtube_id', 'description')
        }),
        ('Media', {
            'fields': ('thumbnail_url', 'duration', 'view_count')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('URLs', {
            'fields': ('youtube_url', 'embed_url'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
