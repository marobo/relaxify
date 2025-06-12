from django.core.management.base import BaseCommand, CommandError
from playlists.models import Playlist
import requests
import re
from django.conf import settings


class Command(BaseCommand):
    help = 'Import YouTube music using YouTube Data API (PythonAnywhere compatible)'

    def add_arguments(self, parser):
        parser.add_argument(
            'urls',
            nargs='+',
            type=str,
            help='YouTube URLs or video IDs to import'
        )
        parser.add_argument(
            '--api-key',
            type=str,
            help='YouTube Data API key (or set YOUTUBE_API_KEY in settings)'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing playlists with new metadata'
        )

    def get_api_key(self, options):
        """Get YouTube API key from options or settings"""
        api_key = options.get('api_key')
        if not api_key:
            api_key = getattr(settings, 'YOUTUBE_API_KEY', None)
        
        if not api_key:
            raise CommandError(
                "YouTube API key required. Set YOUTUBE_API_KEY in settings "
                "or use --api-key option. Get one from: "
                "https://console.developers.google.com/"
            )
        
        return api_key

    def extract_video_id(self, url):
        """Extract YouTube video ID from various URL formats"""
        if len(url) == 11 and re.match(r'^[a-zA-Z0-9_-]+$', url):
            return url
        
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)'
            r'([^&\n?#]+)',
            r'youtube\.com\/watch\?.*v=([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None

    def extract_playlist_id(self, url):
        """Extract YouTube playlist ID from URL"""
        patterns = [
            r'list=([a-zA-Z0-9_-]+)',
            r'playlist\?list=([a-zA-Z0-9_-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None

    def get_playlist_videos(self, playlist_id, api_key):
        """Fetch all video IDs from a playlist using YouTube API"""
        video_ids = []
        next_page_token = None
        
        while True:
            url = 'https://www.googleapis.com/youtube/v3/playlistItems'
            params = {
                'part': 'contentDetails',
                'playlistId': playlist_id,
                'key': api_key,
                'maxResults': 50,
            }
            
            if next_page_token:
                params['pageToken'] = next_page_token
            
            try:
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                for item in data.get('items', []):
                    video_id = item['contentDetails']['videoId']
                    video_ids.append(video_id)
                
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break
                    
            except requests.exceptions.RequestException as e:
                self.stdout.write(
                    self.style.ERROR(f'API Error: {str(e)}')
                )
                break
        
        return video_ids

    def get_video_info(self, video_id, api_key):
        """Fetch video metadata using YouTube Data API"""
        url = 'https://www.googleapis.com/youtube/v3/videos'
        params = {
            'part': 'snippet,statistics,contentDetails',
            'id': video_id,
            'key': api_key,
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('items'):
                return None
            
            item = data['items'][0]
            snippet = item['snippet']
            statistics = item.get('statistics', {})
            content_details = item.get('contentDetails', {})
            
            # Parse duration (ISO 8601 format like PT4M13S)
            duration_iso = content_details.get('duration', 'PT0S')
            duration = self.parse_duration(duration_iso)
            
            description = snippet.get('description', '')
            if len(description) > 500:
                description = description[:500] + '...'
            
            return {
                'title': snippet.get('title', 'Unknown Title'),
                'description': description,
                'thumbnail_url': snippet.get('thumbnails', {}).get(
                    'high', {}
                ).get('url', ''),
                'duration': duration,
                'view_count': int(statistics.get('viewCount', 0)),
                'uploader': snippet.get('channelTitle', ''),
            }
            
        except requests.exceptions.RequestException as e:
            self.stdout.write(
                self.style.ERROR(f'API Error for {video_id}: {str(e)}')
            )
            return None

    def parse_duration(self, duration_iso):
        """Parse ISO 8601 duration to readable format"""
        # PT4M13S -> 4:13
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_iso)
        
        if not match:
            return "0:00"
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

    def handle(self, *args, **options):
        api_key = self.get_api_key(options)
        
        self.stdout.write("=== YouTube Data API Import ===")
        self.stdout.write("Using official YouTube Data API")
        
        urls = options['urls']
        
        # Expand playlist URLs to individual video IDs
        video_ids = []
        for url in urls:
            playlist_id = self.extract_playlist_id(url.strip())
            if playlist_id:
                self.stdout.write(f"Processing playlist: {playlist_id}")
                playlist_videos = self.get_playlist_videos(playlist_id, api_key)
                video_ids.extend(playlist_videos)
                self.stdout.write(
                    f"Found {len(playlist_videos)} videos in playlist"
                )
            else:
                video_id = self.extract_video_id(url.strip())
                if video_id:
                    video_ids.append(video_id)
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Invalid URL or video ID: {url}')
                    )
        
        if not video_ids:
            raise CommandError("No valid video IDs found in provided URLs.")
        
        self.stdout.write(f"Processing {len(video_ids)} YouTube videos...")
        
        created_count = 0
        updated_count = 0
        error_count = 0
        
        for i, video_id in enumerate(video_ids, 1):
            self.stdout.write(f"Processing ({i}/{len(video_ids)}): {video_id}")
            
            # Fetch video information
            video_info = self.get_video_info(video_id, api_key)
            
            if not video_info:
                error_count += 1
                continue
            
            # Check if playlist already exists
            try:
                playlist = Playlist.objects.get(youtube_id=video_id)
                
                if options['update']:
                    # Update existing playlist
                    playlist.title = video_info['title']
                    playlist.description = video_info['description']
                    playlist.thumbnail_url = video_info['thumbnail_url']
                    playlist.duration = video_info['duration']
                    playlist.view_count = video_info['view_count']
                    playlist.save()
                    
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Updated: {playlist.title}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Already exists: {playlist.title}')
                    )
                    
            except Playlist.DoesNotExist:
                # Create new playlist
                playlist_data = {
                    'youtube_id': video_id,
                    'title': video_info['title'],
                    'description': video_info['description'],
                    'thumbnail_url': video_info['thumbnail_url'],
                    'duration': video_info['duration'],
                    'view_count': video_info['view_count'],
                    'is_active': True,
                }
                
                playlist = Playlist.objects.create(**playlist_data)
                created_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f'Created: {playlist.title}')
                )
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS('Import completed!'))
        self.stdout.write(f'Created: {created_count} new playlists')
        self.stdout.write(f'Updated: {updated_count} existing playlists')
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f'Errors: {error_count} failed imports')
            ) 