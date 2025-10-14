// Collection Player JavaScript (Shared between modal and full-page)
let collectionPlayer;
let collectionPlayerModal;
let collectionTracks = [];
let currentCollectionTrackIndex = -1;
let isCollectionPlaying = false;
let isLoop = false;
let isAutoplay = true;
let offlineStorage;
let isOffline = !navigator.onLine;
let collectionData = null;

// Initialize collection player
function initCollectionPlayer(collection, tracks, isModal = false) {
    collectionData = collection;
    collectionTracks = tracks || [];
    
    const prefix = isModal ? 'collection-' : '';
    
    // Update UI elements
    document.getElementById(`${prefix}playlist-title`).textContent = collection.name;
    document.getElementById(`${prefix}playlist-subtitle`).innerHTML = `
        <span class="platform-badge">
            <i class="fab fa-youtube"></i> YouTube
        </span>
        <span class="playlist-count">${collection.playlist_count} tracks</span>
    `;
    
    // Render track list
    renderCollectionTrackList(prefix);
    
    // Initialize offline storage if available
    if (typeof OfflineStorageManager !== 'undefined' && OfflineStorageManager.isSupported()) {
        offlineStorage = new OfflineStorageManager();
        offlineStorage.init();
    }
    
    // Set autoplay button as active by default
    const autoplayBtn = document.getElementById(`${prefix}autoplayBtn`);
    if (autoplayBtn) {
        autoplayBtn.classList.add('active');
        autoplayBtn.title = 'Autoplay: ON';
    }
}

// Collection Player Functions
async function openCollectionPlayer(collectionId, collectionName, platform, trackCount) {
    if (!collectionPlayerModal) {
        collectionPlayerModal = new bootstrap.Modal(document.getElementById('collectionPlayerModal'));
    }
    
    // Update modal title
    document.getElementById('collectionPlayerModalTitle').textContent = collectionName;
    
    // Show loading state
    document.getElementById('collection-track-list').innerHTML = `
        <div style="text-align: center; padding: 2rem; color: #aaa;">
            <div class="spinner"></div>
            <p>Loading tracks...</p>
        </div>
    `;
    
    // Load collection data
    try {
        const response = await fetch(`/api/collections/${collectionId}/`);
        const collectionData = await response.json();
        
        collectionTracks = collectionData.playlists || [];
        
        // Initialize the player
        initCollectionPlayer({
            id: collectionId,
            name: collectionName,
            platform: platform,
            playlist_count: trackCount
        }, collectionTracks, true);
        
        // Show modal
        collectionPlayerModal.show();
        
    } catch (error) {
        console.error('Error loading collection:', error);
        document.getElementById('collection-track-list').innerHTML = `
            <div style="text-align: center; padding: 2rem; color: #ff4444;">
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; margin-bottom: 1rem;"></i>
                <p>Error loading collection</p>
            </div>
        `;
        collectionPlayerModal.show();
    }
}

function renderCollectionTrackList(prefix = '') {
    const trackList = document.getElementById(`${prefix}track-list`);
    
    if (collectionTracks.length === 0) {
        trackList.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: #aaa;">
                <i class="fas fa-music" style="font-size: 2rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                <p>No tracks in this collection</p>
            </div>
        `;
        return;
    }
    
    trackList.innerHTML = collectionTracks.map((track, index) => `
        <div class="track-item" onclick="playCollectionTrack(${index}, '${prefix}')">
            <div class="track-number" id="${prefix}track-number-${index}">
                ${index + 1}
            </div>
            
            ${track.thumbnail_url ? 
                `<img src="${track.thumbnail_url}" alt="${track.title}" class="track-thumbnail">` :
                `<div class="track-thumbnail-placeholder">
                    <i class="fas fa-music" style="font-size: 0.7rem; color: rgba(255,255,255,0.5);"></i>
                </div>`
            }
            
            <div class="track-info">
                <div class="track-title">${track.title}</div>
                <div class="track-artist">${track.artist || 'Unknown Artist'}</div>
            </div>
            
            <div class="track-duration">${track.duration || '--:--'}</div>
        </div>
    `).join('');
}

function playCollectionTrack(index, prefix = '') {
    if (currentCollectionTrackIndex === index && collectionPlayer && isCollectionPlaying) {
        // If same track is playing, just pause/play
        collectionPlayer.pauseVideo();
        return;
    }

    currentCollectionTrackIndex = index;
    const track = collectionTracks[index];
    
    // Update video info
    updateCollectionVideoInfo(track, prefix);
    
    // Update track list UI
    updateCollectionTrackListUI(index, prefix);
    
    // Load YouTube player
    if (collectionPlayer) {
        collectionPlayer.loadVideoById(track.youtube_id);
        hideCollectionLoadingPlaceholder(prefix);
    } else {
        initCollectionYouTubePlayer(track.youtube_id, prefix);
    }
    
    isCollectionPlaying = true;
}

function updateCollectionVideoInfo(track, prefix = '') {
    document.getElementById(`${prefix}current-title`).textContent = track.title;
    document.getElementById(`${prefix}current-artist`).textContent = track.artist || 'Unknown Artist';
    document.getElementById(`${prefix}current-duration`).textContent = track.duration || '--:--';
    document.getElementById(`${prefix}current-views`).textContent = track.view_count ? track.view_count.toLocaleString() : '--';
}

function updateCollectionTrackListUI(playingIndex, prefix = '') {
    // Remove all playing states
    document.querySelectorAll(`#${prefix}track-list .track-item`).forEach((item, index) => {
        item.classList.remove('playing');
        const numberEl = document.getElementById(`${prefix}track-number-${index}`);
        if (numberEl) {
            numberEl.textContent = index + 1;
            numberEl.classList.remove('playing');
        }
    });
    
    // Add playing state to current track
    const currentItem = document.querySelectorAll(`#${prefix}track-list .track-item`)[playingIndex];
    if (currentItem) {
        currentItem.classList.add('playing');
        const numberEl = document.getElementById(`${prefix}track-number-${playingIndex}`);
        if (numberEl) {
            numberEl.innerHTML = '<i class="fas fa-volume-up"></i>';
            numberEl.classList.add('playing');
        }
        
        // Scroll into view
        currentItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

function initCollectionYouTubePlayer(videoId, prefix = '') {
    if (!window.YT) {
        const script = document.createElement('script');
        script.src = 'https://www.youtube.com/iframe_api';
        document.head.appendChild(script);
        
        window.onYouTubeIframeAPIReady = function() {
            createCollectionPlayer(videoId, prefix);
        };
    } else {
        createCollectionPlayer(videoId, prefix);
    }
}

function createCollectionPlayer(videoId, prefix = '') {
    collectionPlayer = new YT.Player(`${prefix}youtube-player`, {
        height: '100%',
        width: '100%',
        videoId: videoId,
        playerVars: {
            'playsinline': 1,
            'rel': 0,
            'modestbranding': 1,
            'controls': 1,
            'showinfo': 0,
            'autoplay': 1
        },
        events: {
            'onStateChange': onCollectionPlayerStateChange
        }
    });
    
    hideCollectionLoadingPlaceholder(prefix);
}

function hideCollectionLoadingPlaceholder(prefix = '') {
    const placeholder = document.getElementById(`${prefix}loading-placeholder`);
    if (placeholder) {
        placeholder.style.display = 'none';
    }
}

function onCollectionPlayerStateChange(event) {
    if (event.data == YT.PlayerState.ENDED) {
        // Auto-play next track
        if (currentCollectionTrackIndex < collectionTracks.length - 1) {
            playCollectionTrack(currentCollectionTrackIndex + 1);
        }
    } else if (event.data == YT.PlayerState.PLAYING) {
        isCollectionPlaying = true;
    } else if (event.data == YT.PlayerState.PAUSED) {
        isCollectionPlaying = false;
    }
}

// Control functions
function shufflePlaylist() {
    if (collectionTracks.length > 0) {
        const randomIndex = Math.floor(Math.random() * collectionTracks.length);
        playCollectionTrack(randomIndex);
    }
}

function toggleLoop() {
    isLoop = !isLoop;
    const loopBtn = document.getElementById('loopBtn') || document.getElementById('collection-loopBtn');
    if (loopBtn) {
        loopBtn.classList.toggle('active', isLoop);
    }
}

function toggleAutoplay() {
    isAutoplay = !isAutoplay;
    const autoplayBtn = document.getElementById('autoplayBtn') || document.getElementById('collection-autoplayBtn');
    if (autoplayBtn) {
        autoplayBtn.classList.toggle('active', isAutoplay);
    }
}

// Stop collection video when modal is closed
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('collectionPlayerModal');
    if (modal) {
        modal.addEventListener('hidden.bs.modal', function() {
            if (collectionPlayer && collectionPlayer.pauseVideo) {
                collectionPlayer.pauseVideo();
            }
            // Reset state
            currentCollectionTrackIndex = -1;
            isCollectionPlaying = false;
        });
    }
});
