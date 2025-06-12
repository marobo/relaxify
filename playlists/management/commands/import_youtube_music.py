from django.core.management.base import BaseCommand, CommandError
from playlists.models import Playlist
import yt_dlp
import re


class Command(BaseCommand):
    help = 'Import your saved YouTube music into playlists'

    def add_arguments(self, parser):
        parser.add_argument(
            'urls',
            nargs='+',
            type=str,
            help='YouTube URLs or video IDs to import'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Path to a file containing YouTube URLs (one per line)'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing playlists with new metadata'
        )
        parser.add_argument(
            '--proxy',
            type=str,
            help='Proxy URL to use for requests (e.g., http://proxy:8080)'
        )
        parser.add_argument(
            '--no-proxy',
            action='store_true',
            help='Disable proxy usage'
        )

    def extract_video_id(self, url):
        """Extract YouTube video ID from various URL formats"""
        # Handle direct video IDs
        if len(url) == 11 and re.match(r'^[a-zA-Z0-9_-]+$', url):
            return url
        
        # Handle various YouTube URL formats
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

    def get_ydl_opts(self, options):
        """Get yt-dlp options with proxy configuration"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
            'skip_download': True,
        }
        
        if options.get('no_proxy'):
            ydl_opts['proxy'] = ''
        elif options.get('proxy'):
            ydl_opts['proxy'] = options['proxy']
        
        return ydl_opts

    def get_playlist_videos(self, playlist_id, options):
        """Fetch all video IDs from a playlist"""
        try:
            playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
            ydl_opts = self.get_ydl_opts(options)
            ydl_opts['extract_flat'] = True
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=False)
                
                if 'entries' not in info:
                    return []
                
                video_ids = []
                for entry in info['entries']:
                    if entry and 'id' in entry:
                        video_ids.append(entry['id'])
                
                return video_ids
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error fetching playlist {playlist_id}: {str(e)}'
                )
            )
            return []

    def get_video_info(self, video_id, options):
        """Fetch video metadata using yt-dlp"""
        try:
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            ydl_opts = self.get_ydl_opts(options)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                
                # Convert duration from seconds to readable format
                duration_seconds = info.get('duration', 0)
                hours = duration_seconds // 3600
                minutes = (duration_seconds % 3600) // 60
                seconds = duration_seconds % 60
                
                if hours > 0:
                    duration = f"{hours}:{minutes:02d}:{seconds:02d}"
                else:
                    duration = f"{minutes}:{seconds:02d}"
                
                description = info.get('description', '')
                if len(description) > 500:
                    description = description[:500] + '...'
                
                return {
                    'title': info.get('title', 'Unknown Title'),
                    'description': description,
                    'thumbnail_url': info.get('thumbnail', ''),
                    'duration': duration,
                    'view_count': info.get('view_count', 0) or 0,
                    'uploader': info.get('uploader', ''),
                }
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error fetching info for {video_id}: {str(e)}'
                )
            )
            return None

    def handle(self, *args, **options):
        urls = []
        
        # Get URLs from command line arguments
        if options['urls']:
            urls.extend(options['urls'])
        
        # Get URLs from file if specified
        if options['file']:
            try:
                with open(options['file'], 'r') as f:
                    file_urls = [line.strip() for line in f if line.strip()]
                    urls.extend(file_urls)
            except FileNotFoundError:
                raise CommandError(f"File not found: {options['file']}")
        
        if not urls:
            raise CommandError(
                "No URLs provided. Use command line arguments or --file option."
            )
        
        # Expand playlist URLs to individual video IDs
        video_ids = []
        for url in urls:
            playlist_id = self.extract_playlist_id(url.strip())
            if playlist_id:
                self.stdout.write(f"Processing playlist: {playlist_id}")
                playlist_videos = self.get_playlist_videos(playlist_id, options)
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
        
        for video_id in video_ids:
            self.stdout.write(f"Processing: {video_id}")
            
            # Fetch video information
            video_info = self.get_video_info(video_id, options)
            
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