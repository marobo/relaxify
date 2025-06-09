from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
import yt_dlp
import os
import tempfile
from .models import Playlist
from .serializers import PlaylistSerializer


# Web Views (Template-based)
def home(request):
    """Home page showing playlist grid"""
    playlists = Playlist.objects.filter(is_active=True)
    return render(request, 'playlists/home.html', {'playlists': playlists})


def detail(request, playlist_id):
    """Detail page for a specific playlist"""
    playlist = get_object_or_404(Playlist, id=playlist_id, is_active=True)
    return render(request, 'playlists/detail.html', {'playlist': playlist})


def offline(request):
    """Offline fallback page"""
    return render(request, 'playlists/offline.html')


# API Views (REST Framework)
class PlaylistListAPIView(generics.ListAPIView):
    """
    API endpoint that returns a list of all active playlists
    """
    queryset = Playlist.objects.filter(is_active=True)
    serializer_class = PlaylistSerializer


class PlaylistDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint that returns a single playlist
    """
    queryset = Playlist.objects.filter(is_active=True)
    serializer_class = PlaylistSerializer


# Audio Download View (Optional Feature)
@csrf_exempt
def download_audio(request, video_id):
    """
    Download audio from YouTube video (for private use only)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        # Validate that the video_id exists in our database
        playlist = get_object_or_404(Playlist, youtube_id=video_id, is_active=True)
        
        # YouTube URL
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': f'{tempfile.gettempdir()}/%(title)s.%(ext)s',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first
            info = ydl.extract_info(youtube_url, download=False)
            title = info.get('title', 'Unknown')
            
            # Download
            ydl.download([youtube_url])
            
            return JsonResponse({
                'success': True,
                'message': f'Audio downloaded: {title}',
                'title': title
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# Service Worker and PWA endpoints
def service_worker(request):
    """Serve the service worker file"""
    return render(request, 'sw.js', content_type='application/javascript')


def manifest(request):
    """Serve the PWA manifest file"""
    return render(request, 'manifest.json', content_type='application/json')


# Add this new view function before the API Views section
@csrf_exempt
def import_youtube(request):
    """
    Web interface for importing YouTube music
    """
    if request.method == 'POST':
        urls_text = request.POST.get('urls', '')
        update_existing = request.POST.get('update_existing') == 'on'
        
        if not urls_text.strip():
            return JsonResponse({'success': False, 'error': 'No URLs provided'})
        
        # Split URLs by lines and clean them
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        
        results = []
        created_count = 0
        updated_count = 0
        error_count = 0
        
        for url in urls:
            try:
                video_id = extract_video_id(url)
                if not video_id:
                    results.append({'url': url, 'status': 'error', 'message': 'Invalid URL'})
                    error_count += 1
                    continue
                
                video_info = get_video_info(video_id)
                if not video_info:
                    results.append({'url': url, 'status': 'error', 'message': 'Could not fetch video info'})
                    error_count += 1
                    continue
                
                # Check if exists
                try:
                    playlist = Playlist.objects.get(youtube_id=video_id)
                    if update_existing:
                        playlist.title = video_info['title']
                        playlist.description = video_info['description']
                        playlist.thumbnail_url = video_info['thumbnail_url']
                        playlist.duration = video_info['duration']
                        playlist.view_count = video_info['view_count']
                        playlist.save()
                        results.append({'url': url, 'status': 'updated', 'title': playlist.title})
                        updated_count += 1
                    else:
                        results.append({'url': url, 'status': 'exists', 'title': playlist.title})
                        
                except Playlist.DoesNotExist:
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
                    results.append({'url': url, 'status': 'created', 'title': playlist.title})
                    created_count += 1
                    
            except Exception as e:
                results.append({'url': url, 'status': 'error', 'message': str(e)})
                error_count += 1
        
        return JsonResponse({
            'success': True,
            'results': results,
            'summary': {
                'created': created_count,
                'updated': updated_count,
                'errors': error_count,
                'total': len(urls)
            }
        })
    
    return render(request, 'playlists/import.html')


def extract_video_id(url):
    """Extract YouTube video ID from various URL formats"""
    import re
    
    # Handle direct video IDs
    if len(url) == 11 and re.match(r'^[a-zA-Z0-9_-]+$', url):
        return url
    
    # Handle various YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def get_video_info(video_id):
    """Fetch video metadata using yt-dlp"""
    try:
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
            'skip_download': True,
        }
        
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
            
            return {
                'title': info.get('title', 'Unknown Title'),
                'description': info.get('description', '')[:500] + ('...' if len(info.get('description', '')) > 500 else ''),
                'thumbnail_url': info.get('thumbnail', ''),
                'duration': duration,
                'view_count': info.get('view_count', 0) or 0,
                'uploader': info.get('uploader', ''),
            }
    except Exception as e:
        return None
