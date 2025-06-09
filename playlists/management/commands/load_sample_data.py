from django.core.management.base import BaseCommand
from playlists.models import Playlist


class Command(BaseCommand):
    help = 'Load sample playlist data for testing'

    def handle(self, *args, **options):
        sample_playlists = [
            {
                'title': 'Peaceful Rain Sounds for Sleep',
                'youtube_id': 'mPZkdNFkNps',
                'description': 'Gentle rain sounds to help you fall asleep and stay asleep. Perfect for relaxation and stress relief.',
                'thumbnail_url': 'https://i.ytimg.com/vi/mPZkdNFkNps/maxresdefault.jpg',
                'duration': '3:00:00',
                'view_count': 15420000,
            },
            {
                'title': 'Meditation Music for Deep Relaxation',
                'youtube_id': 'lFcSrYw-ARY',
                'description': 'Calming meditation music with soft piano and nature sounds. Ideal for meditation, yoga, and mindfulness practice.',
                'thumbnail_url': 'https://i.ytimg.com/vi/lFcSrYw-ARY/maxresdefault.jpg',
                'duration': '2:30:00',
                'view_count': 8750000,
            },
            {
                'title': 'Ocean Waves for Study and Focus',
                'youtube_id': 'WHPEKLQID4U',
                'description': 'Soothing ocean waves sounds to enhance concentration and productivity. Great background noise for studying or working.',
                'thumbnail_url': 'https://i.ytimg.com/vi/WHPEKLQID4U/maxresdefault.jpg',
                'duration': '4:00:00',
                'view_count': 12300000,
            },
            {
                'title': 'Forest Birds Singing - Nature Sounds',
                'youtube_id': 'xNN7iTA57jM',
                'description': 'Beautiful bird songs from a peaceful forest. Perfect for relaxation, meditation, or as background ambiance.',
                'thumbnail_url': 'https://i.ytimg.com/vi/xNN7iTA57jM/maxresdefault.jpg',
                'duration': '1:45:00',
                'view_count': 6890000,
            },
            {
                'title': 'Soft Piano Music for Relaxation',
                'youtube_id': 'jfKfPfyJRdk',
                'description': 'Gentle piano melodies to calm your mind and reduce stress. Ideal for unwinding after a long day.',
                'thumbnail_url': 'https://i.ytimg.com/vi/jfKfPfyJRdk/maxresdefault.jpg',
                'duration': '2:15:00',
                'view_count': 9450000,
            },
            {
                'title': 'Tibetan Singing Bowls Meditation',
                'youtube_id': 'M0ozOGkej94',
                'description': 'Traditional Tibetan singing bowls for deep meditation and spiritual healing. Creates a peaceful atmosphere.',
                'thumbnail_url': 'https://i.ytimg.com/vi/M0ozOGkej94/maxresdefault.jpg',
                'duration': '1:30:00',
                'view_count': 4320000,
            },
        ]

        created_count = 0
        for playlist_data in sample_playlists:
            playlist, created = Playlist.objects.get_or_create(
                youtube_id=playlist_data['youtube_id'],
                defaults=playlist_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created playlist: {playlist.title}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Playlist already exists: {playlist.title}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully loaded {created_count} new playlists')
        ) 