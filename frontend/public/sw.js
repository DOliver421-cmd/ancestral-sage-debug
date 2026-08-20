// Bump this version whenever the app shell changes so the browser is forced
// to reinstall the service worker (a byte-different sw.js always re-fetches).
// Stale service workers + cached index.html are how users stay stuck on old builds.
// NOTE: every PRECACHE entry must be a real, existing route. There is no
// /offline page — including it made `install` fail on a 404.
const CACHE = "wai-v3";
const PRECACHE = ["/", "/login", "/help-center"];

self.addEventListener("install", (event) => {
  // addAll fails the whole install if ONE entry 404s (e.g. a deployment that
  // briefly can't serve the root). allSettled keeps the SW installable so the
  // new logic below actually reaches users; precache failures are non-fatal.
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => Promise.allSettled(PRECACHE.map((url) => cache.add(url))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(clients.claim());
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  // Only http(s) URLs can go into the Cache API. Requests with other schemes
  // (chrome-extension://, chrome://, data:, blob:) would make cache.put() throw
  // "Request scheme 'X' is unsupported" — exactly the console error seen in prod.
  const url = new URL(req.url);
  if (url.protocol !== "http:" && url.protocol !== "https:") return;

  event.respondWith(
    caches.match(req).then((cached) => {
      const fetched = fetch(req).then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE).then((cache) => cache.put(req, clone));
        }
        return response;
      }).catch(() => cached);
      return fetched;
    })
  );
});
