/**
 * Offline Storage Manager for Relaxify
 * Handles IndexedDB operations for offline playback
 */

class OfflineStorageManager {
    constructor() {
        this.dbName = 'RelaxifyOfflineDB';
        this.dbVersion = 1;
        this.db = null;
        this.isOnline = navigator.onLine;
        
        // Listen for online/offline events
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.onOnline();
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.onOffline();
        });
    }

    /**
     * Initialize IndexedDB
     */
    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);
            
            request.onerror = () => {
                console.error('Failed to open IndexedDB:', request.error);
                reject(request.error);
            };
            
            request.onsuccess = () => {
                this.db = request.result;
                console.log('IndexedDB initialized successfully');
                resolve(this.db);
            };
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Create collections store
                if (!db.objectStoreNames.contains('collections')) {
                    const collectionsStore = db.createObjectStore('collections', { keyPath: 'id' });
                    collectionsStore.createIndex('name', 'name', { unique: false });
                    collectionsStore.createIndex('platform', 'platform', { unique: false });
                    collectionsStore.createIndex('lastUpdated', 'lastUpdated', { unique: false });
                }
                
                // Create tracks store
                if (!db.objectStoreNames.contains('tracks')) {
                    const tracksStore = db.createObjectStore('tracks', { keyPath: 'id' });
                    tracksStore.createIndex('collectionId', 'collectionId', { unique: false });
                    tracksStore.createIndex('youtubeId', 'youtubeId', { unique: false });
                    tracksStore.createIndex('title', 'title', { unique: false });
                }
                
                // Create player state store
                if (!db.objectStoreNames.contains('playerState')) {
                    const playerStateStore = db.createObjectStore('playerState', { keyPath: 'id' });
                }
                
                // Create cache metadata store
                if (!db.objectStoreNames.contains('cacheMetadata')) {
                    const cacheStore = db.createObjectStore('cacheMetadata', { keyPath: 'key' });
                }
                
                console.log('IndexedDB schema created/updated');
            };
        });
    }

    /**
     * Save collection and its tracks to IndexedDB
     */
    async saveCollection(collection, tracks) {
        if (!this.db) await this.init();
        
        console.log(`Starting to save collection "${collection.name}" with ${tracks.length} tracks...`);
        
        try {
            // First, clear existing tracks for this collection
            console.log('Clearing existing tracks...');
            await this.clearCollectionTracks(collection.id);
            console.log('Existing tracks cleared');
            
            // Then save collection and tracks in separate transactions
            console.log('Saving collection data...');
            await this.saveCollectionData(collection, tracks);
            console.log('Collection data saved');
            
            // Update cache metadata
            console.log('Updating cache metadata...');
            await this.updateCacheMetadata(`collection_${collection.id}`, {
                lastUpdated: new Date().toISOString(),
                trackCount: tracks.length,
                size: JSON.stringify({ collection, tracks }).length
            });
            console.log('Cache metadata updated');
            
            console.log(`✅ Successfully saved collection "${collection.name}" with ${tracks.length} tracks to offline storage`);
            return true;
        } catch (error) {
            console.error('❌ Error saving collection to offline storage:', error);
            console.error('Error details:', {
                name: error.name,
                message: error.message,
                stack: error.stack
            });
            throw error;
        }
    }

    /**
     * Clear existing tracks for a collection
     */
    async clearCollectionTracks(collectionId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['tracks'], 'readwrite');
            
            transaction.onerror = () => {
                console.error('Transaction error clearing tracks:', transaction.error);
                reject(transaction.error);
            };
            
            transaction.oncomplete = () => {
                resolve();
            };
            
            const tracksStore = transaction.objectStore('tracks');
            const index = tracksStore.index('collectionId');
            const request = index.openCursor(IDBKeyRange.only(collectionId));
            
            request.onsuccess = (event) => {
                const cursor = event.target.result;
                if (cursor) {
                    cursor.delete();
                    cursor.continue();
                }
            };
            
            request.onerror = () => {
                reject(request.error);
            };
        });
    }

    /**
     * Save collection data and tracks
     */
    async saveCollectionData(collection, tracks) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['collections', 'tracks'], 'readwrite');
            
            transaction.onerror = () => {
                console.error('Transaction error saving data:', transaction.error);
                reject(transaction.error);
            };
            
            transaction.oncomplete = () => {
                resolve();
            };
            
            try {
                // Save collection
                const collectionData = {
                    ...collection,
                    lastUpdated: new Date().toISOString(),
                    trackCount: tracks.length
                };
                transaction.objectStore('collections').put(collectionData);
                
                // Save tracks
                const tracksStore = transaction.objectStore('tracks');
                for (const track of tracks) {
                    const trackData = {
                        ...track,
                        collectionId: collection.id,
                        cachedAt: new Date().toISOString()
                    };
                    tracksStore.put(trackData);
                }
            } catch (error) {
                console.error('Error in saveCollectionData:', error);
                reject(error);
            }
        });
    }

    /**
     * Get collection from IndexedDB
     */
    async getCollection(collectionId) {
        if (!this.db) await this.init();
        
        const transaction = this.db.transaction(['collections'], 'readonly');
        const store = transaction.objectStore('collections');
        
        return new Promise((resolve, reject) => {
            const request = store.get(collectionId);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get tracks by collection ID
     */
    async getTracksByCollectionId(collectionId) {
        if (!this.db) await this.init();
        
        const transaction = this.db.transaction(['tracks'], 'readonly');
        const store = transaction.objectStore('tracks');
        const index = store.index('collectionId');
        
        return new Promise((resolve, reject) => {
            const request = index.getAll(collectionId);
            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get all cached collections
     */
    async getAllCollections() {
        if (!this.db) await this.init();
        
        const transaction = this.db.transaction(['collections'], 'readonly');
        const store = transaction.objectStore('collections');
        
        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Save player state
     */
    async savePlayerState(collectionId, state) {
        if (!this.db) await this.init();
        
        const transaction = this.db.transaction(['playerState'], 'readwrite');
        const store = transaction.objectStore('playerState');
        
        const playerState = {
            id: `collection_${collectionId}`,
            collectionId: collectionId,
            currentTrackIndex: state.currentTrackIndex,
            isPlaying: state.isPlaying,
            isLoop: state.isLoop,
            isAutoplay: state.isAutoplay,
            lastPlayedAt: new Date().toISOString(),
            ...state
        };
        
        return new Promise((resolve, reject) => {
            const request = store.put(playerState);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get player state
     */
    async getPlayerState(collectionId) {
        if (!this.db) await this.init();
        
        const transaction = this.db.transaction(['playerState'], 'readonly');
        const store = transaction.objectStore('playerState');
        
        return new Promise((resolve, reject) => {
            const request = store.get(`collection_${collectionId}`);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Update cache metadata
     */
    async updateCacheMetadata(key, metadata) {
        if (!this.db) await this.init();
        
        const transaction = this.db.transaction(['cacheMetadata'], 'readwrite');
        const store = transaction.objectStore('cacheMetadata');
        
        const cacheData = {
            key: key,
            ...metadata,
            updatedAt: new Date().toISOString()
        };
        
        return new Promise((resolve, reject) => {
            const request = store.put(cacheData);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get cache metadata
     */
    async getCacheMetadata(key) {
        if (!this.db) await this.init();
        
        const transaction = this.db.transaction(['cacheMetadata'], 'readonly');
        const store = transaction.objectStore('cacheMetadata');
        
        return new Promise((resolve, reject) => {
            const request = store.get(key);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Check if collection is cached
     */
    async isCollectionCached(collectionId) {
        const metadata = await this.getCacheMetadata(`collection_${collectionId}`);
        return metadata !== undefined;
    }

    /**
     * Get cache size information
     */
    async getCacheInfo() {
        if (!this.db) await this.init();
        
        const collections = await this.getAllCollections();
        const totalTracks = await this.getTotalTrackCount();
        
        return {
            collectionsCount: collections.length,
            totalTracks: totalTracks,
            lastUpdated: collections.length > 0 ? 
                Math.max(...collections.map(c => new Date(c.lastUpdated).getTime())) : null
        };
    }

    /**
     * Get total track count
     */
    async getTotalTrackCount() {
        if (!this.db) await this.init();
        
        const transaction = this.db.transaction(['tracks'], 'readonly');
        const store = transaction.objectStore('tracks');
        
        return new Promise((resolve, reject) => {
            const request = store.count();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Clear all cached data
     */
    async clearAllCache() {
        if (!this.db) await this.init();
        
        try {
            await Promise.all([
                this.clearObjectStore('collections'),
                this.clearObjectStore('tracks'),
                this.clearObjectStore('playerState'),
                this.clearObjectStore('cacheMetadata')
            ]);
            
            console.log('All offline cache cleared');
            return true;
        } catch (error) {
            console.error('Error clearing cache:', error);
            throw error;
        }
    }

    /**
     * Clear an object store
     */
    async clearObjectStore(storeName) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            
            transaction.onerror = () => {
                console.error(`Transaction error clearing ${storeName}:`, transaction.error);
                reject(transaction.error);
            };
            
            transaction.oncomplete = () => {
                resolve();
            };
            
            transaction.objectStore(storeName).clear();
        });
    }

    /**
     * Remove specific collection from cache
     */
    async removeCollection(collectionId) {
        if (!this.db) await this.init();
        
        try {
            // Clear tracks first
            await this.clearCollectionTracks(collectionId);
            
            // Then remove other data in separate transactions
            await Promise.all([
                this.removeCollectionData(collectionId),
                this.removePlayerState(collectionId),
                this.removeCacheMetadata(collectionId)
            ]);
            
            console.log(`Removed collection ${collectionId} from offline cache`);
            return true;
        } catch (error) {
            console.error('Error removing collection from cache:', error);
            throw error;
        }
    }

    /**
     * Remove collection data
     */
    async removeCollectionData(collectionId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['collections'], 'readwrite');
            
            transaction.onerror = () => {
                console.error('Transaction error removing collection:', transaction.error);
                reject(transaction.error);
            };
            
            transaction.oncomplete = () => {
                resolve();
            };
            
            transaction.objectStore('collections').delete(collectionId);
        });
    }

    /**
     * Remove player state
     */
    async removePlayerState(collectionId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['playerState'], 'readwrite');
            
            transaction.onerror = () => {
                console.error('Transaction error removing player state:', transaction.error);
                reject(transaction.error);
            };
            
            transaction.oncomplete = () => {
                resolve();
            };
            
            transaction.objectStore('playerState').delete(`collection_${collectionId}`);
        });
    }

    /**
     * Remove cache metadata
     */
    async removeCacheMetadata(collectionId) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['cacheMetadata'], 'readwrite');
            
            transaction.onerror = () => {
                console.error('Transaction error removing cache metadata:', transaction.error);
                reject(transaction.error);
            };
            
            transaction.oncomplete = () => {
                resolve();
            };
            
            transaction.objectStore('cacheMetadata').delete(`collection_${collectionId}`);
        });
    }

    /**
     * Handle going online
     */
    onOnline() {
        console.log('Back online - syncing data...');
        this.showNotification('Back online - syncing data...', 'success');
        
        // Trigger sync if service worker is available
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({
                type: 'REQUEST_SYNC'
            });
        }
    }

    /**
     * Handle going offline
     */
    onOffline() {
        console.log('Gone offline - using cached data');
        this.showNotification('You are offline - using cached data', 'warning');
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        const bgColor = type === 'success' ? '#1db954' : 
                       type === 'warning' ? '#f59e0b' : 
                       type === 'error' ? '#ff4444' : '#333';
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${bgColor};
            color: white;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            z-index: 9999;
            font-size: 0.9rem;
            opacity: 0;
            transition: opacity 0.3s;
            max-width: 300px;
        `;
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <i class="fas fa-${type === 'success' ? 'check' : 
                                  type === 'warning' ? 'exclamation-triangle' : 
                                  type === 'error' ? 'times' : 'info'}"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => notification.style.opacity = '1', 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    /**
     * Check if browser supports required features
     */
    static isSupported() {
        return 'indexedDB' in window && 'serviceWorker' in navigator;
    }
}

// Export for use in other files
window.OfflineStorageManager = OfflineStorageManager;
