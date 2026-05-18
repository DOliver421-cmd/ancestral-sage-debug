// W.A.I. Service Worker
// CACHE version — bump this string any time you want to force all clients to
// drop the old cache and re-fetch everything (happens automatically on deploy
// when Render's build hash changes, but an explicit bump guarantees it).
const CACHE = "wai-v3";

// Hashed static assets (JS/CSS bundles from CRA) can be cached aggressively
// because their filenames change with every build.
const HASHED_ASSET = /\/static\/(js|css|media)\/.+\.[a-f0-9]{8,}\.(js|css|chunk\.js|chunk\.css|png|svg|woff2?)$/;

self.addEventListener("install", (e) => {
  // Don't pre-cache anything on install — fetch fresh on first use.
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  // Delete every cache that isn't the current version.
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Pass-through: non-GET, API calls, WebSocket upgrade
  if (
    request.method !== "GET" ||
    url.pathname.startsWith("/api/") ||
    url.pathname.includes("/ws/")
  ) return;

  // HTML navigation requests (index.html / SPA shell) — ALWAYS network-first.
  // This is the critical rule: after a deploy the SW must never serve a stale
  // index.html because it will reference old JS bundle filenames that 404.
  if (request.mode === "navigate" || url.pathname === "/" || url.pathname.endsWith(".html")) {
    event.respondWith(
      fetch(request)
        .then((resp) => {
          if (resp && resp.status === 200) {
            const copy = resp.clone();
            caches.open(CACHE).then((c) => c.put(request, copy)).catch(() => {});
          }
          return resp;
        })
        .catch(() => caches.match(request).then((c) => c || caches.match("/")))
    );
    return;
  }

  // Hashed static assets (JS/CSS bundles) — cache-first, safe because the
  // filename itself changes with every build.
  if (HASHED_ASSET.test(url.pathname)) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((resp) => {
          if (resp && resp.status === 200) {
            const copy = resp.clone();
            caches.open(CACHE).then((c) => c.put(request, copy)).catch(() => {});
          }
          return resp;
        });
      })
    );
    return;
  }

  // Everything else (manifest, icons, fonts, etc.) — network-first with cache fallback.
  event.respondWith(
    fetch(request)
      .then((resp) => {
        if (resp && resp.status === 200 && resp.type !== "opaque") {
          const copy = resp.clone();
          caches.open(CACHE).then((c) => c.put(request, copy)).catch(() => {});
        }
        return resp;
      })
      .catch(() => caches.match(request))
  );
});
