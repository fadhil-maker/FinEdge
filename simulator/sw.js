// FinEdge Service Worker — enables offline caching and true PWA install
const CACHE_NAME = 'finedge-v1';
const ASSETS = [
  './',
  './index.html',
  './nexus.html',
  './fedmobile.html',
  './aura.html',
  './engine.js',
  './manifest.json',
  './icon-192.png',
  './icon-512.png'
];

// Install: cache all core assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

// Activate: clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch: serve from cache first, fall back to network
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});
