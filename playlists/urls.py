from django.urls import path
from . import views

app_name = 'playlists'

urlpatterns = [
    # Web views
    path('', views.home, name='home'),
    path('playlist/<int:playlist_id>/', views.detail, name='detail'),
    path('import/', views.import_youtube, name='import'),
    path('offline/', views.offline, name='offline'),
    
    # API endpoints
    path('api/playlists/', views.PlaylistListAPIView.as_view(), name='playlist-list-api'),
    path('api/playlists/<int:pk>/', views.PlaylistDetailAPIView.as_view(), name='playlist-detail-api'),
    
    # Download functionality
    path('download/<str:video_id>/', views.download_audio, name='download_audio'),
    
    # PWA files
    path('sw.js', views.service_worker, name='service_worker'),
    path('manifest.json', views.manifest, name='manifest'),
] 