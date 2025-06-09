# Relaxify 🎵

A Progressive Web App (PWA) for relaxing YouTube playlists with offline support and push notifications.

## Features

- 🎵 **Curated Playlists**: Browse relaxing YouTube music playlists
- 📱 **PWA Support**: Installable app with offline capabilities
- 🌐 **Offline Access**: Save playlists for offline viewing
- 🔔 **Push Notifications**: Get notified about new content
- 💾 **Audio Download**: Optional private audio downloads
- 🎨 **Responsive Design**: Mobile-first, beautiful UI
- 🗄️ **IndexedDB**: Client-side storage for offline data

## Tech Stack

### Backend
- **Django 5.2+**: Web framework
- **Django REST Framework**: API endpoints
- **django-webpush**: Push notifications
- **yt-dlp**: YouTube audio downloads
- **SQLite**: Database (development)

### Frontend
- **HTML5/CSS3**: Modern web standards
- **Bootstrap 5**: Responsive UI framework
- **Vanilla JavaScript**: PWA functionality
- **Service Worker**: Offline caching and background sync
- **IndexedDB**: Client-side data storage

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd relaxify

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data
python manage.py load_sample_data
```

### 3. Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` to see the app!

## Project Structure

```
relaxify/
├── playlists/              # Main Django app
│   ├── models.py          # Playlist model
│   ├── views.py           # Web and API views
│   ├── serializers.py     # DRF serializers
│   ├── admin.py           # Admin configuration
│   └── management/        # Custom commands
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   ├── playlists/        # App templates
│   ├── sw.js             # Service Worker
│   └── manifest.json     # PWA Manifest
├── static/               # Static files
├── relaxify/             # Django project settings
└── requirements.txt      # Python dependencies
```

## API Endpoints

- `GET /api/playlists/` - List all playlists
- `GET /api/playlists/{id}/` - Get playlist details
- `POST /download/{video_id}/` - Download audio (optional)
- `/webpush/` - Push notification endpoints

## PWA Features

### Service Worker (`/sw.js`)
- Caches static assets and API responses
- Provides offline functionality
- Handles background sync
- Manages push notifications

### Manifest (`/manifest.json`)
- App metadata and icons
- Installation prompts
- App shortcuts
- Theme colors

### IndexedDB
- Stores playlist data offline
- Enables offline browsing
- Syncs when back online

## Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key
DEBUG=True
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_ADMIN_EMAIL=admin@yourdomain.com
```

### Generate VAPID Keys

For push notifications, generate VAPID keys:

```bash
# Install web-push CLI
npm install -g web-push

# Generate keys
web-push generate-vapid-keys
```

## Deployment

### Production Settings

1. Set `DEBUG=False`
2. Configure `ALLOWED_HOSTS`
3. Set up proper database (PostgreSQL recommended)
4. Configure static files serving
5. Set up HTTPS (required for PWA)
6. Generate and set VAPID keys

### Static Files

```bash
python manage.py collectstatic
```

### Database Migration

```bash
python manage.py migrate
```

## Usage

### Adding Playlists

1. Access Django admin at `/admin/`
2. Add new playlists with YouTube video IDs
3. Users can save playlists for offline use

### Offline Functionality

1. Users can save playlists while online
2. Saved playlists are accessible offline
3. App works offline with cached content

### Push Notifications

1. Users can subscribe to notifications
2. Admin can send notifications about new content
3. Notifications work even when app is closed

## Development

### Adding New Features

1. Models: Update `playlists/models.py`
2. API: Add views in `playlists/views.py`
3. Frontend: Update templates and JavaScript
4. PWA: Modify service worker as needed

### Testing

```bash
# Run Django tests
python manage.py test

# Test PWA features in browser dev tools
# Check Application tab for:
# - Service Worker registration
# - Cache storage
# - IndexedDB data
# - Manifest validation
```

## Legal & Security

- Audio downloads are for **private use only**
- Respect YouTube's Terms of Service
- No public redistribution of downloaded content
- HTTPS required for PWA features
- Secure handling of user data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational purposes. Please respect YouTube's Terms of Service and copyright laws.

## Support

For issues and questions:
1. Check the Django and PWA documentation
2. Review browser console for errors
3. Test PWA features in supported browsers
4. Ensure HTTPS for production PWA features

---

**Made with ❤️ for relaxation and learning** # relaxify
