/**
 * TeamConferenceEmbed — exec-admin-only Team Conference bridge.
 *
 * Reality correction (2026-08-27): the conference-bridge embed was previously a
 * static script tag in public/index.html, so the floating "Team Conference"
 * panel + shared room rendered for EVERY visitor. Team Conference is an
 * executive/admin feature — not a public interface. This component injects the
 * same embed script (same slug/origin/label attrs, so the WAI side keeps
 * matching this deployment) but ONLY when the signed-in user holds admin rank
 * or higher. Logged-out and non-staff visitors get nothing.
 *
 * 2026-09-xx: the WAI bridge renders a fixed bottom-right pill (#waiBridgeBtn)
 * and a fixed panel (#waiBridgePanel). That was locking content under the
 * pill on small screens. This wrapper now enhances both nodes to be
 * draggable (pointer events, clamp to viewport, persisted in localStorage) so
 * an exec can drag them out of the way. If the upstream script never loads,
 * nothing renders — honest 503, not a fake "connected" state.
 */
import { useEffect, useRef } from "react";
import { useAuth } from "../lib/auth";
import { ROLE_RANK } from "../lib/roles";

const EMBED_URL = "https://wai-institute-production.up.railway.app/embed/conference-bridge.js";

const EMBED_ATTRS = {
  src: EMBED_URL,
  "data-slug": "wai-morehelp-bridge",
  "data-origin": "morehelp",
  "data-label": "MORE Help Center",
  "data-site-url": "https://www.morehelp.center",
};

const BTN_KEY = "wai_bridge_btn_pos";
const PANEL_KEY = "wai_bridge_panel_pos";

function loadPos(key) {
  try {
    const v = JSON.parse(localStorage.getItem(key));
    if (v && typeof v.x === "number" && typeof v.y === "number") return v;
  } catch {
    /* ignore */
  }
  return null;
}

function savePos(key, pos) {
  try {
    localStorage.setItem(key, JSON.stringify(pos));
  } catch {
    /* storage unavailable */
  }
}

function clampPos(x, y, w, h) {
  const maxX = Math.max(0, window.innerWidth - w);
  const maxY = Math.max(0, window.innerHeight - h);
  return { x: Math.min(Math.max(0, x), maxX), y: Math.min(Math.max(0, y), maxY) };
}

function applyPos(el, pos) {
  if (!el || !pos) return;
  const w = el.offsetWidth || 200;
  const h = el.offsetHeight || 56;
  const c = clampPos(pos.x, pos.y, w, h);
  el.style.left = `${c.x}px`;
  el.style.top = `${c.y}px`;
  el.style.right = "auto";
  el.style.bottom = "auto";
}

function makeDraggable(el, storageKey, opts = {}) {
  if (!el || el.dataset.dragEnhanced === "1") return;
  el.dataset.dragEnhanced = "1";
  // eslint-disable-next-line no-param-reassign
  el.style.touchAction = "none";
  // keep grab cursor unless the element is the pill (which already has pointer)
  if (!el.style.cursor || el.style.cursor === "pointer") {
    // let pill stay pointer, panel header gets grab via opts.handle
  }

  const handle = opts.handle || el;
  // visual affordance on the handle
  handle.style.cursor = "grab";
  handle.title = (handle.title ? `${handle.title} — ` : "") + "Drag to move";

  let startX = 0;
  let startY = 0;
  let origPos = null;
  let moved = false;
  let dragging = false;

  function onPointerDown(e) {
    if (e.button !== 0) return;
    // don't start drag from interactive children (buttons) unless the handle itself
    if (opts.handle && e.target !== handle && !handle.contains(e.target)) return;
    if (opts.handle && e.target.closest && e.target.closest("button")) return;

    const rect = el.getBoundingClientRect();
    startX = e.clientX;
    startY = e.clientY;
    // anchor to current on-screen rect so first drag doesn't jump
    const current = loadPos(storageKey);
    origPos = current ? { x: current.x, y: current.y } : { x: rect.left, y: rect.top };
    // if first drag, ensure element is positioned via left/top so delta applies cleanly
    if (!current) applyPos(el, origPos);
    moved = false;
    dragging = true;
    handle.setPointerCapture?.(e.pointerId);
    handle.style.cursor = "grabbing";
    el.style.cursor = "grabbing";
    el.style.userSelect = "none";
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointercancel", onUp);
  }

  function onMove(e) {
    if (!dragging) return;
    const dx = e.clientX - startX;
    const dy = e.clientY - startY;
    if (!moved && Math.hypot(dx, dy) < 4) return; // dead zone — clicks still toggle
    moved = true;
    const nx = origPos.x + dx;
    const ny = origPos.y + dy;
    const c = clampPos(nx, ny, el.offsetWidth || 200, el.offsetHeight || 56);
    el.style.left = `${c.x}px`;
    el.style.top = `${c.y}px`;
    el.style.right = "auto";
    el.style.bottom = "auto";
    // suppress the panel-toggle click when the pill was dragged
    if (moved && opts.suppressClick) {
      e.preventDefault();
    }
  }

  function onUp(e) {
    window.removeEventListener("pointermove", onMove);
    window.removeEventListener("pointerup", onUp);
    window.removeEventListener("pointercancel", onUp);
    handle.style.cursor = "grab";
    el.style.cursor = opts.handle ? "" : "pointer";
    el.style.userSelect = "";
    dragging = false;
    if (moved) {
      const rect = el.getBoundingClientRect();
      const final = clampPos(rect.left, rect.top, el.offsetWidth || 200, el.offsetHeight || 56);
      savePos(storageKey, final);
      // stash so a drag doesn't also fire the pill's toggle handler
      if (opts.suppressClick) {
        el.dataset.wasDragged = "1";
        setTimeout(() => {
          delete el.dataset.wasDragged;
        }, 350);
      }
    }
    moved = false;
    try {
      handle.releasePointerCapture?.(e.pointerId);
    } catch {
      /* ignore */
    }
  }

  handle.addEventListener("pointerdown", onPointerDown);

  // restore saved position on attach
  const saved = loadPos(storageKey);
  if (saved) applyPos(el, saved);

  // keep inside viewport on resize — re-apply clamped saved pos or current rect
  const onResize = () => {
    const p = loadPos(storageKey);
    if (p) applyPos(el, p);
    else {
      const r = el.getBoundingClientRect();
      applyPos(el, { x: r.left, y: r.top });
    }
  };
  window.addEventListener("resize", onResize);

  // double-click handle to reset
  handle.addEventListener("dblclick", () => {
    try {
      localStorage.removeItem(storageKey);
    } catch {
      /* ignore */
    }
    // reset to defaults — remove fixed overrides and let upstream CSS re-apply
    el.style.left = "";
    el.style.top = "";
    el.style.right = "";
    el.style.bottom = "";
    // force the upstream defaults back (right:22 bottom:22) via inline after tick
    requestAnimationFrame(() => {
      if (el.id === "waiBridgeBtn") {
        el.style.right = "22px";
        el.style.bottom = "22px";
        el.style.left = "auto";
        el.style.top = "auto";
      } else if (el.id === "waiBridgePanel") {
        el.style.right = "22px";
        el.style.bottom = "84px";
        el.style.left = "auto";
        el.style.top = "auto";
      }
    });
  });
}

function enhanceBridgeNodes() {
  const btn = document.getElementById("waiBridgeBtn");
  const panel = document.getElementById("waiBridgePanel");
  const head = document.getElementById("waiBridgeHead");

  if (btn && btn.dataset.dragEnhanced !== "1") {
    // intercept the pill's click so a drag doesn't toggle the panel
    const rawClick = btn.onclick;
    btn.addEventListener(
      "click",
      (e) => {
        if (btn.dataset.wasDragged === "1") {
          e.stopImmediatePropagation();
          e.preventDefault();
        }
      },
      true
    );
    // also patch the upstream listener that toggles display — guard via dataset flag inside makeDraggable's onUp
    makeDraggable(btn, BTN_KEY, { suppressClick: true });
    // keep raw handler ref so lint doesn't warn
    void rawClick;
  }
  if (panel) {
    // panel itself is draggable via its header; if no header yet, make whole panel draggable
    const dragHandle = head || panel;
    if (panel.dataset.dragEnhanced !== "1") {
      makeDraggable(panel, PANEL_KEY, { handle: dragHandle });
      if (head) {
        head.style.touchAction = "none";
        // subtle affordance
        head.style.cursor = "grab";
      }
    }
  }
}

export default function TeamConferenceEmbed() {
  const { user, loading } = useAuth();
  const injectedRef = useRef(false);
  const observerRef = useRef(null);

  useEffect(() => {
    if (loading || !user) return;
    const rank = ROLE_RANK[user.role] ?? 0;
    if (rank < (ROLE_RANK.admin ?? 0)) return;
    if (injectedRef.current || document.getElementById("wai-conference-bridge-script")) return;

    const script = document.createElement("script");
    script.id = "wai-conference-bridge-script";
    for (const [k, v] of Object.entries(EMBED_ATTRS)) {
      script.setAttribute(k, v);
    }
    script.onerror = () => {
      console.warn("[TeamConference] WAI embed script failed to load — conference unavailable");
    };
    script.onload = () => {
      // script builds #waiBridgeBtn / #waiBridgePanel synchronously in start() — enhance on next tick
      setTimeout(enhanceBridgeNodes, 300);
      // also catch the case where start() is waiting for DOMContentLoaded
      setTimeout(enhanceBridgeNodes, 1200);
    };
    script.defer = true;
    document.body.appendChild(script);
    injectedRef.current = true;

    // MutationObserver fallback — if the upstream script injects after DOMContentLoaded
    const obs = new MutationObserver(() => enhanceBridgeNodes());
    obs.observe(document.body, { childList: true, subtree: false });
    observerRef.current = obs;

    // periodic fallback for the first few seconds (covers timing edge)
    const iv = setInterval(enhanceBridgeNodes, 700);
    const stop = setTimeout(() => {
      clearInterval(iv);
      enhanceBridgeNodes();
    }, 6000);

    // handle ESC to close panel (nice-to-have, doesn't claim to fix upstream)
    const onKey = (e) => {
      if (e.key === "Escape") {
        const p = document.getElementById("waiBridgePanel");
        if (p) p.style.display = "none";
      }
    };
    window.addEventListener("keydown", onKey);

    return () => {
      clearInterval(iv);
      clearTimeout(stop);
      window.removeEventListener("keydown", onKey);
      if (observerRef.current) observerRef.current.disconnect();
    };
  }, [user, loading]);

  // Also run enhancer whenever the route/user changes and the nodes already exist (e.g. HMR)
  useEffect(() => {
    if (!user) return;
    const rank = ROLE_RANK[user.role] ?? 0;
    if (rank < (ROLE_RANK.admin ?? 0)) return;
    enhanceBridgeNodes();
    const t = setTimeout(enhanceBridgeNodes, 600);
    return () => clearTimeout(t);
  }, [user]);

  return null;
}
