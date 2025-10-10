/**
 * Test script for offline functionality
 * Run this in the browser console to test offline storage
 */

async function testOfflineStorage() {
    console.log('🧪 Testing Offline Storage...');
    
    // Check if OfflineStorageManager is available
    if (typeof OfflineStorageManager === 'undefined') {
        console.error('❌ OfflineStorageManager not found. Make sure offline-storage.js is loaded.');
        return;
    }
    
    try {
        // Initialize storage
        const storage = new OfflineStorageManager();
        await storage.init();
        console.log('✅ OfflineStorageManager initialized');
        
        // Test data
        const testCollection = {
            id: 999,
            name: 'Test Collection',
            platform: 'youtube',
            playlist_count: 2
        };
        
        const testTracks = [
            {
                id: 1001,
                youtube_id: 'test1',
                title: 'Test Track 1',
                artist: 'Test Artist',
                duration: '3:45',
                view_count: 1000,
                thumbnail_url: 'https://example.com/thumb1.jpg'
            },
            {
                id: 1002,
                youtube_id: 'test2',
                title: 'Test Track 2',
                artist: 'Test Artist',
                duration: '4:20',
                view_count: 2000,
                thumbnail_url: 'https://example.com/thumb2.jpg'
            }
        ];
        
        // Test saving collection
        console.log('💾 Testing save collection...');
        await storage.saveCollection(testCollection, testTracks);
        console.log('✅ Collection saved successfully');
        
        // Wait a moment for transaction to complete
        await new Promise(resolve => setTimeout(resolve, 100));
        
        // Test retrieving collection
        console.log('📖 Testing retrieve collection...');
        const retrievedCollection = await storage.getCollection(testCollection.id);
        console.log('✅ Collection retrieved:', retrievedCollection);
        
        // Test retrieving tracks
        console.log('🎵 Testing retrieve tracks...');
        const retrievedTracks = await storage.getTracksByCollectionId(testCollection.id);
        console.log('✅ Tracks retrieved:', retrievedTracks.length, 'tracks');
        
        // Test saving player state
        console.log('🎮 Testing save player state...');
        await storage.savePlayerState(testCollection.id, {
            currentTrackIndex: 1,
            isPlaying: true,
            isLoop: false,
            isAutoplay: true
        });
        console.log('✅ Player state saved');
        
        // Test retrieving player state
        console.log('📱 Testing retrieve player state...');
        const playerState = await storage.getPlayerState(testCollection.id);
        console.log('✅ Player state retrieved:', playerState);
        
        // Test cache info
        console.log('📊 Testing cache info...');
        const cacheInfo = await storage.getCacheInfo();
        console.log('✅ Cache info:', cacheInfo);
        
        // Test checking if collection is cached
        console.log('🔍 Testing is collection cached...');
        const isCached = await storage.isCollectionCached(testCollection.id);
        console.log('✅ Is cached:', isCached);
        
        // Clean up test data
        console.log('🧹 Cleaning up test data...');
        await storage.removeCollection(testCollection.id);
        console.log('✅ Test data cleaned up');
        
        console.log('🎉 All offline storage tests passed!');
        
    } catch (error) {
        console.error('❌ Test failed:', error);
    }
}

// Auto-run test if in browser console
if (typeof window !== 'undefined') {
    console.log('🚀 Offline Storage Test Suite');
    console.log('Run testOfflineStorage() to test offline functionality');
    
    // Make test function globally available
    window.testOfflineStorage = testOfflineStorage;
}
