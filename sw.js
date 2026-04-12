/**
 * Terra Balance – Service Worker
 * Caches the game for offline play after first load.
 */

const CACHE_NAME = 'terra-balance-v1';
const OFFLINE_URL = '/terra-balance/';

// Resources to pre-cache on install
const PRE_CACHE = [
  '/terra-balance/',
  '/terra-balance/index.html',
  '/terra-balance/manifest.json',
  '/terra-balance/icons/icon-192.png',
  '/terra-balance/icons/icon-512.png',
];

// ── Install ──────────────────────────────────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(PRE_CACHE).catch(err => {
        // Don't fail install if some assets are missing
        console.warn('[SW] Pre-cache partial failure:', err);
      });
    })
  );
  self.skipWaiting();
});

// ── Activate ─────────────────────────────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// ── Fetch ─────────────────────────────────────────────────────────────────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET and cross-origin CDN requests (Three.js etc.) — let them go
  // through normally so we always get the latest version.
  if (request.method !== 'GET') return;
  if (url.origin !== self.location.origin) return;

  // Network-first for navigation (ensures fresh game content)
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then(response => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
          return response;
        })
        .catch(() => caches.match(OFFLINE_URL))
    );
    return;
  }

  // Cache-first for static assets (icons, manifest, etc.)
  event.respondWith(
    caches.match(request).then(cached => {
      if (cached) return cached;
      return fetch(request).then(response => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
        }
        return response;
      });
    })
  );
});
