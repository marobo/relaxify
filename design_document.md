# Relaxify
Relaxing YouTube Playlist Web App with Offline & Push Support

1. 📌 Project Overview
Relaxify is a Progressive Web App (PWA) built with Django backend and modern frontend technologies. It lets users browse curated YouTube playlists of relaxing music, access them offline, receive push notifications when new videos are added, and optionally download audio for private use.

2. 🎯 Objectives
Provide a relaxing YouTube music playlist experience
Support offline access via PWA capabilities and IndexedDB
Push notifications for new content
Private download of YouTube audio (for offline listening)
Responsive mobile-first design

3. 🏗️ Architecture Overview
Frontend (PWA)
HTML5, CSS3 (Bootstrap)

JavaScript (vanilla + Service Worker)

IndexedDB for storing playlists offline

Manifest.json for PWA

Service Worker for:

Caching app shell and assets

Background sync for playlist updates

Push notifications

Backend (Django)
Django for core views and routing

Django REST Framework for playlist API

django-webpush for push notifications

yt-dlp for private audio downloads

SQLite or Postgres for database

4. 🔧 Features
Feature	Description
🎵 Playlist View Users can browse curated playlists fetched from the database
📲 Installable App	Via PWA manifest and service worker
🌐 Offline Support	Static assets + dynamic content cached for offline use
🔄 Background Sync	Playlists updated automatically when back online
🔔 Push Notifications	Notify users when new content is added
💾 Audio Download	Allow optional download of audio (private use only)
🧠 IndexedDB	Stores playlist data for instant offline use

5. 🧩 Components
5.1 Models (Django)
```
class Playlist(models.Model):
    title = models.CharField(max_length=200)
    youtube_id = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
```
5.2 API (Django REST Framework)
/api/playlists/ – Returns a JSON list of all playlist entries

5.3 Templates
home.html – Shows playlist list

detail.html – Plays a YouTube video (embed or player)

offline.html – Offline fallback page

5.4 Service Worker (sw.js)
Handles:

App shell caching

Dynamic caching

Background sync for /api/playlists/

Push notification handler

5.5 IndexedDB Schema
js
```
// DB: relaxify-db
// Store: playlists
{
  id: Number,
  title: String,
  youtube_id: String,
  description: String
}
```
5.6 Push Notifications
Uses django-webpush to subscribe users

Stores subscriptions in DB

Sends notification on new playlist/video via:

```
send_user_notification(user=user, payload=payload, ttl=1000)
```
5.7 Audio Download (Optional)
Route:

path("download/<str:video_id>/", download_audio, name="download_audio")
```
Uses yt-dlp to fetch and convert video to MP3.

6. 🔐 Security & Legal
Audio downloads are optional and for private use only

Downloads must respect YouTube Terms of Service

No public audio hosting

7. 🧪 Test ing Strategy
Type	   Tool	    Description
Unit Tests	Django TestCase	For models & views
API Tests	DRF’s APIClient	Validate /api/playlists/
PWA Tests	Chrome Lighthouse	Test offline + installability
Manual Testing	Browser Dev Tools	Verify caching, push, sync

8. 🚀 Deployment Plan
Item	Platform
Web Hosting	PythonAnywhere / DigitalOcean
Static Files	WhiteNoise or CDN
HTTPS	Required for PWA, Push
Background Tasks	Django Q / Celery (optional)

9. 📱 UX Design
Pages:
Home (playlist grid)

Video Player

Offline Page

Notifications UI

Optional download buttons

Design principles:

Clean, calm UI (relaxation focus)

Mobile-first layout

Accessible controls

10. ✅ Future Enhancements
Playlist categories (e.g., sleep, study, meditation)

User login with favorite playlists

Spotify / SoundCloud integration

Scheduled audio notifications

✅ Status Checklist
Feature	Done
Django backend	
Playlist model/API	
PWA manifest	
Service Worker	
Offline caching	
Background sync	
Push notifications	
Optional download	
Responsive UI	
IndexedDB	