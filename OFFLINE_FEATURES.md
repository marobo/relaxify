# Offline Features for Relaxify

This document describes the offline functionality implemented in Relaxify, allowing users to save playlists and play music while offline.

## Features

### 🎵 Save Playlists for Offline Use
- Save entire playlists to IndexedDB for offline access
- Preserve track metadata, thumbnails, and playlist information
- Automatic caching with visual indicators

### 📱 Offline Player
- Play cached playlists without internet connection
- Maintain player state (current track, loop, autoplay settings)
- Visual indicators for offline mode and cached content

### 🔄 Online/Offline Sync
- Automatic detection of online/offline status
- Seamless switching between online and offline modes
- Background sync when connection is restored

### 🗂️ Offline Manager
- View all cached collections
- Manage offline storage
- Remove cached playlists to free up space

## Technical Implementation

### IndexedDB Schema

The offline storage uses IndexedDB with the following structure:

#### Collections Store
- **Key**: `id` (collection ID)
- **Data**: Collection metadata, platform, track count, last updated timestamp

#### Tracks Store
- **Key**: `id` (track ID)
- **Indexes**: `collectionId`, `youtubeId`, `title`
- **Data**: Track metadata, YouTube ID, title, artist, duration, views, thumbnail

#### Player State Store
- **Key**: `collection_${collectionId}`
- **Data**: Current track index, playing state, loop/autoplay settings

#### Cache Metadata Store
- **Key**: `collection_${collectionId}`
- **Data**: Cache size, last updated, track count

### Service Worker Integration

The service worker handles:
- Caching collection data for offline access
- Background sync when online
- API request interception for offline scenarios

### Browser Compatibility

**Supported Browsers:**
- Chrome 24+
- Firefox 16+
- Safari 7+
- Edge 12+

**Required Features:**
- IndexedDB support
- Service Worker support
- ES6 Promises

## Usage

### Saving a Playlist for Offline

1. Navigate to any collection player page
2. Click the "Save for Offline" button (download icon)
3. Wait for the save to complete
4. The playlist is now available offline

### Playing Offline

1. When offline, cached playlists will automatically load
2. Track information and metadata are available
3. Video playback requires internet connection (YouTube limitation)
4. Player controls work normally

### Managing Offline Content

1. Go to the Offline Manager from the home page
2. View all cached collections
3. Remove collections to free up storage space
4. Monitor cache usage and statistics

## API Reference

### OfflineStorageManager Class

#### Methods

```javascript
// Initialize the storage manager
await offlineStorage.init()

// Save collection and tracks
await offlineStorage.saveCollection(collection, tracks)

// Get collection data
const collection = await offlineStorage.getCollection(collectionId)

// Get tracks for a collection
const tracks = await offlineStorage.getTracksByCollectionId(collectionId)

// Save player state
await offlineStorage.savePlayerState(collectionId, state)

// Get player state
const state = await offlineStorage.getPlayerState(collectionId)

// Check if collection is cached
const isCached = await offlineStorage.isCollectionCached(collectionId)

// Get cache information
const info = await offlineStorage.getCacheInfo()

// Remove collection from cache
await offlineStorage.removeCollection(collectionId)

// Clear all cached data
await offlineStorage.clearAllCache()
```

### Events

The offline storage manager listens for:
- `online` - When browser comes back online
- `offline` - When browser goes offline

## Storage Limits

### Browser Storage Quotas
- **Chrome**: ~50% of available disk space
- **Firefox**: ~50% of available disk space  
- **Safari**: ~1GB by default
- **Edge**: ~50% of available disk space

### Recommended Limits
- Maximum 100 collections cached
- Maximum 10,000 tracks total
- Regular cleanup of unused collections

## Troubleshooting

### Common Issues

**"Offline storage not supported"**
- Browser doesn't support IndexedDB or Service Workers
- Use a modern browser (Chrome, Firefox, Safari, Edge)

**"Failed to save for offline"**
- Storage quota exceeded
- Clear some cached data or use a different browser

**"No cached data available"**
- Collection wasn't saved for offline use
- Save the collection while online first

**Video playback not working offline**
- YouTube videos require internet connection
- This is a limitation of YouTube's API, not the app
- **What works offline**: Track browsing, metadata, playlists, player controls
- **What requires internet**: Actual video/audio streaming from YouTube

### Debug Mode

Enable debug logging by opening browser console and running:
```javascript
localStorage.setItem('relaxify-debug', 'true')
```

### Testing Offline Functionality

Run the test suite in browser console:
```javascript
testOfflineStorage()
```

## Security Considerations

- All data is stored locally in the browser
- No sensitive data is transmitted
- Cached data is isolated per browser/device
- Users can clear all cached data at any time

## Performance Notes

- IndexedDB operations are asynchronous
- Large playlists may take time to save
- Cache size affects browser performance
- Regular cleanup recommended

## Future Enhancements

- Audio file caching for true offline playback
- Background sync improvements
- Cross-device sync capabilities
- Advanced cache management
- Offline analytics and usage tracking
