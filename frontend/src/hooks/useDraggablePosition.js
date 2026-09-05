import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Makes a floating widget draggable and persists its position.
 *
 * Returns:
 *   pos       — { x, y } current position (px from top-left)
 *   onPointerDown — attach to the widget's drag handle / root element
 *   dragged   — true once the user has dragged (buttons can suppress click)
 *   reset     — restore default position
 *
 * Position persists per storageKey so the layout survives reloads.
 * Clamps to the viewport on drag and on window resize.
 */
export default function useDraggablePosition(storageKey, defaultPos) {
  const [pos, setPos] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey));
      if (saved && typeof saved.x === "number" && typeof saved.y === "number") return saved;
    } catch {
      /* fall through to default */
    }
    return defaultPos;
  });
  const [dragged, setDragged] = useState(false);
  const dragState = useRef(null);

  const clamp = useCallback((x, y, el) => {
    const w = el?.offsetWidth || 56;
    const h = el?.offsetHeight || 56;
    const maxX = Math.max(0, window.innerWidth - w);
    const maxY = Math.max(0, window.innerHeight - h);
    return { x: Math.min(Math.max(0, x), maxX), y: Math.min(Math.max(0, y), maxY) };
  }, []);

  useEffect(() => {
    const onResize = () => setPos((p) => clamp(p.x, p.y, null));
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [clamp]);

  const onPointerDown = useCallback(
    (e) => {
      if (e.button !== 0) return;
      const el = e.currentTarget;
      const startX = e.clientX;
      const startY = e.clientY;
      // If no position has been set yet (CSS-placed), anchor to the element's
      // current on-screen position so the first drag moves it from where it is.
      const origPos = pos || (() => {
        const r = el.getBoundingClientRect();
        return { x: r.left, y: r.top };
      })();
      let moved = false;
      dragState.current = { el, startX, startY, origPos };

      const onMove = (ev) => {
        const dx = ev.clientX - startX;
        const dy = ev.clientY - startY;
        if (!moved && Math.hypot(dx, dy) < 4) return; // dead zone so clicks still work
        moved = true;
        setDragged(true);
        setPos(clamp(origPos.x + dx, origPos.y + dy, el));
      };
      const onUp = () => {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
        dragState.current = null;
        if (moved) {
          setPos((p) => {
            const final = clamp(p.x, p.y, el);
            localStorage.setItem(storageKey, JSON.stringify(final));
            return final;
          });
        }
      };
      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
    },
    [pos, clamp, storageKey]
  );

  const reset = useCallback(() => {
    setPos(defaultPos);
    localStorage.removeItem(storageKey);
    setDragged(false);
  }, [defaultPos, storageKey]);

  return { pos, onPointerDown, dragged, reset };
}
