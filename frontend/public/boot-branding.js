// boot-branding.js — domain-aware initial paint branding (see
// docs/morehelp-migration-blueprint.md). The SPA rewrites title/meta per route
// at runtime (src/lib/seo.js); this tiny script handles the first paint so
// wai-institute.org never flashes M.O.R.E. branding before React mounts, and
// non-JS crawlers get the correct door's default.
(function () {
  try {
    if (window.location.hostname.indexOf("wai-institute.org") !== -1) {
      document.title = "WAI Institute — Electrical Education & Credentials";
      var set = function (attr, name, content) {
        var el = document.querySelector("meta[" + attr + '="' + name + '"]');
        if (el) el.setAttribute("content", content);
      };
      set("name", "description", "Trade training that pays, credentials that verify, and media skills that move the message. Electrical education, NFPA 70 / NEC 2023 compliance, and AI Tutor.");
      set("property", "og:site_name", "WAI Institute");
      set("property", "og:title", "WAI Institute — Electrical Education & Credentials");
      set("property", "og:description", "Electrical education, NFPA 70 / NEC 2023 compliance training, verified credentials, and AI Tutor.");
      set("property", "og:image", "https://www.wai-institute.org/wai-og-1200x630.png");
      set("property", "og:url", window.location.href);
      set("name", "twitter:title", "WAI Institute — Electrical Education & Credentials");
      set("name", "twitter:description", "Electrical education, NFPA 70 / NEC 2023 compliance training, verified credentials, and AI Tutor.");
      set("name", "twitter:image", "https://www.wai-institute.org/wai-og-1200x630.png");
    }
  } catch (e) { /* never block render on branding */ }
})();
