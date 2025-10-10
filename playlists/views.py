from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework import generics
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import redirect
from .forms import LoginForm, SignupForm

import yt_dlp
import tempfile
import re
from .models import Playlist, PlaylistCollection, UserPlaylistCollection
from .serializers import (
    PlaylistSerializer, PlaylistCollectionSerializer,
    PlaylistCollectionSummarySerializer, UserPlaylistCollectionSerializer
)

import requests


# Web Views (Template-based)
def home(request):
    """Home page showing playlist collections and individual tracks"""
    # Get filter parameter from URL
    filter_type = request.GET.get('filter', 'all')  # all, collections, tracks

    # Get collections and individual tracks
    collections = PlaylistCollection.objects.filter(is_active=True)
    individual_tracks = Playlist.objects.filter(
        is_active=True, collection__isnull=True
    )[:20]

    # Apply filtering based on filter_type
    if filter_type == 'collections':
        individual_tracks = []
    elif filter_type == 'tracks':
        collections = []
    # If filter_type is 'all', show both (no filtering needed)

    return render(request, 'playlists/home.html', {
        'collections': collections,
        'individual_tracks': individual_tracks,
        'current_filter': filter_type
    })


def collection_player(request, collection_id):
    """Full-screen playlist player for a collection"""
    collection = get_object_or_404(PlaylistCollection, id=collection_id, is_active=True)
    tracks = collection.playlists.filter(is_active=True)
    return render(request, 'playlists/collection_player.html', {
        'collection': collection,
        'tracks': tracks
    })


def detail(request, playlist_id):
    """Detail page for a specific track"""
    playlist = get_object_or_404(Playlist, id=playlist_id, is_active=True)
    return render(request, 'playlists/detail.html', {'playlist': playlist})


def offline(request):
    """Offline fallback page"""
    return render(request, 'playlists/offline.html')


# API Views (REST Framework)
class PlaylistListAPIView(generics.ListAPIView):
    """API endpoint that returns a list of all active tracks"""
    queryset = Playlist.objects.filter(is_active=True)
    serializer_class = PlaylistSerializer


class PlaylistDetailAPIView(generics.RetrieveAPIView):
    """API endpoint that returns a single track"""
    queryset = Playlist.objects.filter(is_active=True)
    serializer_class = PlaylistSerializer


class PlaylistDeleteAPIView(generics.DestroyAPIView):
    """API endpoint to delete a track"""
    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer


class PlaylistCollectionListAPIView(generics.ListAPIView):
    """API endpoint that returns a list of all active playlist collections"""
    queryset = PlaylistCollection.objects.filter(is_active=True)
    serializer_class = PlaylistCollectionSummarySerializer


class PlaylistCollectionDetailAPIView(generics.RetrieveAPIView):
    """API endpoint that returns a single playlist collection with all tracks"""
    queryset = PlaylistCollection.objects.filter(is_active=True)
    serializer_class = PlaylistCollectionSerializer


class UserPlaylistCollectionListAPIView(generics.ListAPIView):
    """API endpoint that returns user playlist collections"""
    queryset = UserPlaylistCollection.objects.filter(is_public=True)
    serializer_class = UserPlaylistCollectionSerializer


# Audio Download View (Optional Feature)
@csrf_exempt
def download_audio(request, video_id):
    """Download audio from YouTube video (for private use only)"""
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
    return render(request, 'static/js/sw.js', content_type='application/javascript')


def manifest(request):
    """Serve the PWA manifest file"""
    return render(request, 'manifest.json', content_type='application/json')


@csrf_exempt
@login_required
def import_youtube(request):
    """Enhanced web interface for importing YouTube videos and playlists"""
    if request.method == 'POST':
        urls_text = request.POST.get('urls', '')
        update_existing = request.POST.get('update_existing') == 'on'
        import_mode = request.POST.get('import_mode', 'individual')  # individual, playlist
        collection_name = request.POST.get('collection_name', '').strip()

        if not urls_text.strip():
            return JsonResponse({'success': False, 'error': 'No URLs provided'})

        # Split URLs by lines and clean them
        urls = [url.strip() for url in urls_text.split('\n') if url.strip()]

        results = []
        created_count = 0
        updated_count = 0
        error_count = 0
        collection = None

        # Create collection if needed
        if import_mode in ['playlist'] and collection_name:
            platform = 'youtube'
            collection, created = PlaylistCollection.objects.get_or_create(
                name=collection_name,
                defaults={
                    'platform': platform,
                    'description': f'Imported {platform} collection'
                }
            )

        for url in urls:
            try:
                if import_mode == 'playlist':
                    # Handle YouTube playlist import
                    playlist_id = extract_playlist_id(url)
                    if playlist_id:
                        result = import_youtube_playlist(playlist_id, collection, update_existing)
                        results.extend(result['results'])
                        created_count += result['created_count']
                        updated_count += result['updated_count']
                        error_count += result['error_count']
                    else:
                        results.append({'url': url, 'status': 'error', 'message': 'Invalid playlist URL'})
                        error_count += 1
                else:
                    # Handle individual video import (existing functionality)
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
                            update_playlist_from_info(playlist, video_info, collection, 'youtube')
                            results.append({'url': url, 'status': 'updated', 'title': playlist.title})
                            updated_count += 1
                        else:
                            results.append({'url': url, 'status': 'exists', 'title': playlist.title})

                    except Playlist.DoesNotExist:
                        playlist = create_playlist_from_info(video_id, video_info, collection, 'youtube')
                        results.append({'url': url, 'status': 'created', 'title': playlist.title})
                        created_count += 1

            except Exception as e:
                results.append({'url': url, 'status': 'error', 'message': str(e)})
                error_count += 1

        return JsonResponse({
            'success': True,
            'results': results,
            'collection': collection.name if collection else None,
            'summary': {
                'created': created_count,
                'updated': updated_count,
                'errors': error_count,
                'total': len(urls)
            }
        })

    return render(request, 'playlists/import.html')


def extract_playlist_id(url):
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


def create_playlist_from_info(video_id, video_info, collection=None, platform='youtube'):
    """Create a new Playlist object from video info"""
    playlist_data = {
        'youtube_id': video_id,
        'title': video_info['title'],
        'description': video_info['description'],
        'thumbnail_url': video_info['thumbnail_url'],
        'duration': video_info['duration'],
        'duration_seconds': video_info.get('duration_seconds'),
        'view_count': video_info['view_count'],
        'artist': video_info.get('uploader', ''),
        'platform_source': platform,
        'collection': collection,
        'is_active': True,
    }
    return Playlist.objects.create(**playlist_data)


def update_playlist_from_info(playlist, video_info, collection=None, platform='youtube'):
    """Update an existing Playlist object with new info"""
    playlist.title = video_info['title']
    playlist.description = video_info['description']
    playlist.thumbnail_url = video_info['thumbnail_url']
    playlist.duration = video_info['duration']
    playlist.duration_seconds = video_info.get('duration_seconds')
    playlist.view_count = video_info['view_count']
    playlist.artist = video_info.get('uploader', '')
    if collection:
        playlist.collection = collection
    playlist.platform_source = platform
    playlist.save()


def extract_video_id(url):
    """Extract YouTube video ID from various URL formats"""
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


def youtube_api_request(endpoint, params):
    """Helper to call the YouTube Data API v3"""
    base_url = 'https://www.googleapis.com/youtube/v3/'
    params['key'] = settings.YOUTUBE_API_KEY
    response = requests.get(base_url + endpoint, params=params)
    response.raise_for_status()
    return response.json()


def get_video_info(video_id):
    """Fetch video metadata using YouTube Data API v3"""
    try:
        data = youtube_api_request('videos', {
            'part': 'snippet,contentDetails,statistics',
            'id': video_id
        })
        if not data['items']:
            return None
        info = data['items'][0]
        snippet = info['snippet']
        statistics = info.get('statistics', {})
        content_details = info.get('contentDetails', {})
        # Parse ISO 8601 duration
        import isodate
        duration_seconds = int(isodate.parse_duration(content_details.get('duration', 'PT0S')).total_seconds())
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        seconds = duration_seconds % 60
        if hours > 0:
            duration = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            duration = f"{minutes}:{seconds:02d}"
        return {
            'title': snippet.get('title', 'Unknown Title'),
            'description': snippet.get('description', '')[:500] + ('...' if len(snippet.get('description', '')) > 500 else ''),
            'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
            'duration': duration,
            'duration_seconds': duration_seconds,
            'view_count': int(statistics.get('viewCount', 0)),
            'uploader': snippet.get('channelTitle', ''),
        }
    except Exception as e:
        return None


def import_youtube_playlist(playlist_id, collection=None, update_existing=False):
    """Import all videos from a YouTube playlist using YouTube Data API v3"""
    results = []
    created_count = 0
    updated_count = 0
    error_count = 0
    try:
        # Get playlist metadata
        playlist_data = youtube_api_request('playlists', {
            'part': 'snippet',
            'id': playlist_id
        })
        if playlist_data['items']:
            snippet = playlist_data['items'][0]['snippet']
            if collection:
                collection.youtube_playlist_id = playlist_id
                if not collection.name or collection.name.startswith('Imported'):
                    collection.name = snippet.get('title', collection.name)
                if snippet.get('description'):
                    collection.description = snippet['description'][:500]
                if snippet.get('thumbnails', {}).get('high', {}).get('url'):
                    collection.thumbnail_url = snippet['thumbnails']['high']['url']
                collection.save()
        # Get all video IDs in the playlist (may require pagination)
        next_page_token = None
        video_ids = []
        while True:
            params = {
                'part': 'contentDetails',
                'playlistId': playlist_id,
                'maxResults': 50
            }
            if next_page_token:
                params['pageToken'] = next_page_token
            page = youtube_api_request('playlistItems', params)
            for item in page.get('items', []):
                video_id = item['contentDetails']['videoId']
                video_ids.append(video_id)
            next_page_token = page.get('nextPageToken')
            if not next_page_token:
                break
        # Process each video
        for video_id in video_ids:
            try:
                video_info = get_video_info(video_id)
                if not video_info:
                    results.append({'video_id': video_id, 'status': 'error', 'message': 'Could not fetch video info'})
                    error_count += 1
                    continue
                try:
                    playlist = Playlist.objects.get(youtube_id=video_id)
                    if update_existing:
                        update_playlist_from_info(playlist, video_info, collection, 'youtube')
                        results.append({'video_id': video_id, 'status': 'updated', 'title': playlist.title})
                        updated_count += 1
                    else:
                        results.append({'video_id': video_id, 'status': 'exists', 'title': playlist.title})
                except Playlist.DoesNotExist:
                    playlist = create_playlist_from_info(video_id, video_info, collection, 'youtube')
                    results.append({'video_id': video_id, 'status': 'created', 'title': playlist.title})
                    created_count += 1
            except Exception as e:
                results.append({'video_id': video_id, 'status': 'error', 'message': str(e)})
                error_count += 1
    except Exception as e:
        return {
            'results': [{'url': f'https://www.youtube.com/playlist?list={playlist_id}', 'status': 'error', 'message': str(e)}],
            'created_count': 0,
            'updated_count': 0,
            'error_count': 1
        }
    return {
        'results': results,
        'created_count': created_count,
        'updated_count': updated_count,
        'error_count': error_count
    }


def auth_toggle_view(request):
    template_name = 'auth_toggle.html'
    if request.method == 'GET':
        login_form = LoginForm(request)
        signup_form = SignupForm()
        form_to_show = 'login'
        next_url = request.GET.get('next', '')
        return render(request, template_name, {
            'login_form': login_form,
            'signup_form': signup_form,
            'form_to_show': form_to_show,
            'next': next_url,
        })
    else:  # POST
        login_form = LoginForm(request, data=request.POST)
        signup_form = SignupForm(request.POST)
        form_to_show = 'login'
        next_url = request.POST.get('next', '')

        if 'login' in request.POST:
            form_to_show = 'login'
            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)
                if next_url:
                    return redirect(next_url)
                return redirect('playlists:home')

        elif 'signup' in request.POST:
            form_to_show = 'signup'
            if signup_form.is_valid():
                user = signup_form.save(commit=False)
                user.set_password(signup_form.cleaned_data['password'])
                user.save()
                login(request, user)
                if next_url:
                    return redirect(next_url)
                return redirect('playlists:home')

        return render(request, template_name, {
            'login_form': login_form,
            'signup_form': signup_form,
            'form_to_show': form_to_show,
            'next': next_url,
        })
