const CACHE_NAME = 'relaxify-v1';
const STATIC_CACHE = 'relaxify-static-v1';
const DYNAMIC_CACHE = 'relaxify-dynamic-v1';

// Files to cache for offline use
const STATIC_FILES = [
    '/',
    '/offline/',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// Install event - cache static files
self.addEventListener('install', event => {
    console.log('Service Worker: Installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('Service Worker: Caching static files');
                return cache.addAll(STATIC_FILES);
            })
            .catch(error => {
                console.error('Service Worker: Error caching static files', error);
            })
    );
    
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker: Activating...');
    
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                        console.log('Service Worker: Deleting old cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    
    self.clients.claim();
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Handle API requests
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(handleApiRequest(request));
        return;
    }
    
    // Handle navigation requests
    if (request.mode === 'navigate') {
        event.respondWith(handleNavigationRequest(request));
        return;
    }
    
    // Handle other requests (static files, etc.)
    event.respondWith(handleStaticRequest(request));
});

// Handle API requests
async function handleApiRequest(request) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        return new Response(JSON.stringify({ error: 'Offline and no cached data available' }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// Handle navigation requests
async function handleNavigationRequest(request) {
    try {
        const networkResponse = await fetch(request);
        return networkResponse;
    } catch (error) {
        const offlineResponse = await caches.match('/offline/');
        if (offlineResponse) {
            return offlineResponse;
        }
        
        return new Response('Offline', { status: 503 });
    }
}

// Handle static requests
async function handleStaticRequest(request) {
    try {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        return new Response('Resource not available offline', { status: 503 });
    }
}

// Background sync for playlist updates
self.addEventListener('sync', event => {
    console.log('Service Worker: Background sync triggered', event.tag);
    
    if (event.tag === 'playlist-sync') {
        event.waitUntil(syncPlaylists());
    }
});

// Sync playlists when back online
async function syncPlaylists() {
    try {
        console.log('Service Worker: Syncing playlists...');
        
        // Fetch latest playlists from API
        const response = await fetch('/api/playlists/');
        if (response.ok) {
            const playlists = await response.json();
            
            // Update cache with latest data
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put('/api/playlists/', new Response(JSON.stringify(playlists)));
            
            // Notify clients about the update
            const clients = await self.clients.matchAll();
            clients.forEach(client => {
                client.postMessage({
                    type: 'PLAYLISTS_UPDATED',
                    data: playlists
                });
            });
            
            console.log('Service Worker: Playlists synced successfully');
        }
    } catch (error) {
        console.error('Service Worker: Error syncing playlists', error);
    }
}

// Message handler for communication with main thread
self.addEventListener('message', event => {
    console.log('Service Worker: Message received', event.data);
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'REQUEST_SYNC') {
        // Register background sync
        self.registration.sync.register('playlist-sync');
    }
}); 