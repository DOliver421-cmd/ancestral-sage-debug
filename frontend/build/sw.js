// Bump this version whenever the app shell changes so the browser is forced
// to reinstall the service worker (a byte-different sw.js always re-fetches).
// Stale service workers + cached index.html are how users stay stuck on old builds.
// NOTE: every PRECACHE entry must be a real, existing route. There is no
// /offline page — including it made `install` fail on a 404.
const CACHE = "wai-v6";
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
  event.waitUntil((async () => {
    // Drop every cache that is not the current version. Without this, a
    // version bump leaves the previous generation's entries — including its
    // index.html pointing at a retired bundle hash — in place forever, and a
    // browser that already registered that worker keeps loading the old shell.
    const names = await caches.keys();
    await Promise.all(names.filter((n) => n !== CACHE).map((n) => caches.delete(n)));
    await clients.claim();
  })());
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  if (url.protocol !== "http:" && url.protocol !== "https:") return;

  // FIRST-PARTY ONLY. The handler used to intercept every cross-origin GET as
  // well (Google Fonts, Fontshare, Pexels images, the conference-bridge
  // script). Those requests are blocked by the page's own connect-src CSP, the
  // rejection was caught, `cached` was undefined, and the handler resolved to
  // `undefined` — which makes respondWith throw "Failed to convert value to
  // 'Response'" and the fetch fails. Letting the browser serve cross-origin
  // requests itself is both correct and CSP-honest; this worker caches our own
  // app shell and assets.
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    caches.match(req).then((cached) => {
      const fetched = fetch(req)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE).then((cache) => cache.put(req, clone));
          }
          return response;
        })
        // A network failure with nothing cached must resolve to a real
        // Response, never undefined (see the comment above).
        .catch(() => cached || new Response("", {
          status: 504, statusText: "Offline",
        }));
      return fetched;
    })
  );
});
