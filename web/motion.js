/* Living Interface (backlog B-01): motion that answers a real event, and nothing else. No loop runs here:
   every change is a class or attribute set in answer to an event (a request sent or answered, a page
   rendered, the tab hidden or shown), and the CSS in core/tokens.css animates only transform and opacity.

   - focus(keys): briefly mark the page elements an answer was read from. Elements carry
     data-focus="key …"; an SVG mark also dims its siblings. Nothing found = nothing happens.
   - after(keys): the same, once the next page has rendered (the shell sends “mf:page”).
   - While the tab is hidden, animations pause (html[data-hidden]) and a highlight waits until it is shown.
   - Reduced motion: the CSS drops every animation; a highlight is a still outline for the same time. */

const HOLD = 2600;  // ms a highlight stays: long enough to find it, short enough not to linger
let waiting = null, queued = null, clear = null;
const running = new Set();  // Web Animations started by charts (Sankey flow dots): paused with the tab

document.addEventListener("visibilitychange", () => { for (const a of running) document.hidden ? a.pause() : a.play(); });

/* Keep a Web Animation in step with the tab: paused while hidden, forgotten when it ends. */
export function track(anim) {
  running.add(anim);
  if (document.hidden) anim.pause();
  anim.finished.then(() => running.delete(anim), () => running.delete(anim));
  return anim;
}

export const reduced = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

function marks(keys) {
  const found = [];
  for (const k of keys || []) {
    for (const el of document.querySelectorAll(`[data-focus~="${CSS.escape(k)}"]`)) {
      if (!el.closest("[hidden]") && el.getClientRects().length) found.push(el);
    }
  }
  return found;
}

/* How many elements for `keys` are on the page now (nothing is marked). */
export const present = (keys) => marks(keys).length;

/* Mark the elements for `keys`; returns how many were found. Later calls replace earlier marks. */
export function focus(keys, {scroll = true} = {}) {
  const els = marks(keys);
  if (!els.length) return 0;
  if (document.hidden) { queued = keys; return els.length; }  // shown when the tab is visible again
  if (clear) clear();
  const dimmed = new Set();
  for (const el of els) {
    el.classList.add("mf-focus");
    const svg = el instanceof SVGElement && el.ownerSVGElement;
    if (svg) { svg.classList.add("mf-dim"); dimmed.add(svg); }
  }
  window.dispatchEvent(new CustomEvent("mf:focus", {detail: {keys}}));  // a page may add its own (graph: the path)
  if (scroll) {
    const r = els[0].getBoundingClientRect();
    if (r.top < 64 || r.bottom > innerHeight - 24) els[0].scrollIntoView({block: "center", behavior: reduced() ? "auto" : "smooth"});
  }
  const timer = setTimeout(() => clear && clear(), HOLD);
  clear = () => {
    clearTimeout(timer);
    for (const el of els) el.classList.remove("mf-focus");
    for (const svg of dimmed) svg.classList.remove("mf-dim");
    clear = null;
  };
  return els.length;
}

/* Highlight `keys` once the next page has rendered (an evidence link, a Copilot navigation). */
export function after(keys) { waiting = keys && keys.length ? keys : null; }

export function start() {
  const root = document.documentElement;
  const vis = () => {
    root.toggleAttribute("data-hidden", document.hidden);
    if (!document.hidden && queued) { const k = queued; queued = null; focus(k); }
  };
  document.addEventListener("visibilitychange", vis);
  vis();
  window.addEventListener("mf:page", () => {
    if (!waiting) return;
    const k = waiting; waiting = null;
    requestAnimationFrame(() => focus(k));  // one frame: the page's own layout first
  });
}
