// FinEdge Service Worker v2 — forces cache refresh
const CACHE_NAME = 'finedge-v2';
const ASSETS = [
  './',
  './index.html',
  './nexus.html',
  './fedmobile.html',
  './aura.html',
  './engine.js',
  './manifest.json',
  './manifest-nexus.json',
  './manifest-fedmobile.json',
  './manifest-aura.json',
  './icon-192.png',
  './icon-512.png',
  './icon-nexus-192.png',
  './icon-nexus-512.png',
  './icon-fedmobile-192.png',
  './icon-fedmobile-512.png',
  './icon-aura-192.png',
  './icon-aura-512.png'
];

// Install: cache all core assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

// Activate: delete ALL old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch: network-first for HTML, cache-first for assets
self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate' || event.request.url.endsWith('.html')) {
    // Always fetch fresh HTML from network
    event.respondWith(
      fetch(event.request).then((response) => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        return response;
      }).catch(() => caches.match(event.request))
    );
  } else {
    event.respondWith(
      caches.match(event.request).then((cached) => cached || fetch(event.request))
    );
  }
});
