from rest_framework import serializers
from .models import Playlist, PlaylistCollection, UserPlaylistCollection


class PlaylistSerializer(serializers.ModelSerializer):
    """
    Serializer for Playlist model
    """
    youtube_url = serializers.ReadOnlyField()
    embed_url = serializers.ReadOnlyField()
    collection_name = serializers.CharField(source='collection.name', read_only=True)

    class Meta:
        model = Playlist
        fields = [
            'id', 'title', 'artist', 'album', 'track_number',
            'youtube_id', 'description', 'thumbnail_url',
            'duration', 'duration_seconds', 'view_count',
            'platform_source', 'collection', 'collection_name',
            'youtube_url', 'embed_url',
            'created', 'updated'
        ]


class PlaylistCollectionSerializer(serializers.ModelSerializer):
    playlists = PlaylistSerializer(many=True, read_only=True)
    playlist_count = serializers.ReadOnlyField()
    total_duration_formatted = serializers.ReadOnlyField()
    
    class Meta:
        model = PlaylistCollection
        fields = [
            'id', 'name', 'description', 'platform',
            'youtube_playlist_id', 'thumbnail_url',
            'playlist_count', 'total_duration_formatted',
            'playlists', 'created', 'updated'
        ]


class PlaylistCollectionSummarySerializer(serializers.ModelSerializer):
    """Lighter serializer for listing collections without all tracks"""
    playlist_count = serializers.ReadOnlyField()
    total_duration_formatted = serializers.ReadOnlyField()
    
    class Meta:
        model = PlaylistCollection
        fields = [
            'id', 'name', 'description', 'platform',
            'youtube_playlist_id', 'thumbnail_url',
            'playlist_count', 'total_duration_formatted',
            'created', 'updated'
        ]


class UserPlaylistCollectionSerializer(serializers.ModelSerializer):
    collections = PlaylistCollectionSummarySerializer(many=True, read_only=True)
    tracks = PlaylistSerializer(many=True, read_only=True)
    total_tracks = serializers.ReadOnlyField()
    
    class Meta:
        model = UserPlaylistCollection
        fields = [
            'id', 'name', 'description', 'is_public',
            'collections', 'tracks', 'total_tracks',
            'created', 'updated'
        ] 