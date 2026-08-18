// Bump this version whenever the app shell changes so the browser is forced
// to reinstall the service worker (a byte-different sw.js always re-fetches).
// Stale service workers + cached index.html are how users stay stuck on old builds.
const CACHE = "wai-v2";
const PRECACHE = ["/", "/login", "/help-center"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(clients.claim());
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(
    caches.match(event.request).then((cached) => {
      const fetched = fetch(event.request).then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE).then((cache) => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => cached);
      return fetched;
    })
  );
});
