from django.urls import path
from . import views

app_name = 'playlists'

urlpatterns = [
    # Web views
    path('', views.home, name='home'),
    path('import/', views.import_youtube, name='import'),
    path('track/<int:playlist_id>/', views.detail, name='detail'),
    path('collection/<int:collection_id>/', views.collection_detail, name='collection_detail'),
    path('player/<int:collection_id>/', views.collection_player, name='collection_player'),
    path('offline/', views.offline, name='offline'),
    
    # API endpoints for tracks
    path('api/tracks/', views.PlaylistListAPIView.as_view(), name='api-tracks-list'),
    path('api/tracks/<int:pk>/', views.PlaylistDetailAPIView.as_view(), name='api-tracks-detail'),
    path('api/tracks/<int:pk>/delete/', views.PlaylistDeleteAPIView.as_view(), name='api-tracks-delete'),
    
    # API endpoints for collections
    path('api/collections/', views.PlaylistCollectionListAPIView.as_view(), name='api-collections-list'),
    path('api/collections/<int:pk>/', views.PlaylistCollectionDetailAPIView.as_view(), name='api-collections-detail'),
    
    # API endpoints for user collections
    path('api/user-collections/', views.UserPlaylistCollectionListAPIView.as_view(), name='api-user-collections-list'),
    
    # Download endpoint
    path('download/<str:video_id>/', views.download_audio, name='download_audio'),
    
    # PWA endpoints
    path('sw.js', views.service_worker, name='service_worker'),
    path('manifest.json', views.manifest, name='manifest'),
] 