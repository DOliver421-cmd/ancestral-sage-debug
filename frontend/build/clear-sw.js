// Runs before the app boots. Clears any broken/stale SW registration so the
// updated sw.js installs cleanly on next page load.
(function () {
  if (!('serviceWorker' in navigator)) return;

  var SW_SCRIPT = '/sw.js';
  var MANAGED = false; // set true when we find our own registration

  navigator.serviceWorker.getRegistrations().then(function (regs) {
    var staleUnregistered = false;
    regs.forEach(function (reg) {
      var scriptURL = (reg.active || reg.installing || reg.waiting || {}).scriptURL || '';
      if (scriptURL.includes(SW_SCRIPT)) {
        MANAGED = true; // our SW — leave it; sw.js handles its own upgrade
      } else {
        // Foreign or zombie SW — remove it
        reg.unregister();
        staleUnregistered = true;
      }
    });

    if (staleUnregistered) {
      // Clear all caches left behind by the zombie SW, then reload once so the
      // fresh SW installs and the page gets clean assets.
      caches.keys().then(function (names) {
        return Promise.all(names.map(function (n) { return caches.delete(n); }));
      }).then(function () {
        // Guard against reload loops: only reload if we haven't just done so.
        if (!sessionStorage.getItem('sw_cleared')) {
          sessionStorage.setItem('sw_cleared', '1');
          window.location.reload(true);
        }
      });
    }
  }).catch(function () {});
}());
