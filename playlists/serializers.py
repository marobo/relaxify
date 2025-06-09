from rest_framework import serializers
from .models import Playlist


class PlaylistSerializer(serializers.ModelSerializer):
    """
    Serializer for Playlist model
    """
    youtube_url = serializers.ReadOnlyField()
    embed_url = serializers.ReadOnlyField()

    class Meta:
        model = Playlist
        fields = [
            'id',
            'title',
            'youtube_id',
            'description',
            'thumbnail_url',
            'duration',
            'view_count',
            'created',
            'updated',
            'is_active',
            'youtube_url',
            'embed_url'
        ] 