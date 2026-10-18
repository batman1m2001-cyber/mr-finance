/* The dock's fold and divider (FEAT-40 panel UX; shared with the staff desks, FEAT-41): the fold button, the divider on
   the dock's left edge (drag, arrows, Home/End, Enter folds, a double-click or ↺ back to the default), the width kept
   per browser under ``key``. The caller passes what to do while a drag holds the centre (the Customer's graph holds
   its layout and scales its SVG layers: ``hold``, ``canvas``) and after the layout changes (``redraw``). */
import {$} from "../core/core.js";

export function dockFrame(root, {key = "mf.ws", canvas, hold = () => {}, redraw = () => {}} = {}) {
  const setFold = (folded) => {
    root.classList.toggle("folded", folded);
    $("#ws-fold", root).setAttribute("aria-expanded", String(!folded));
    try { localStorage.setItem(`${key}.fold`, folded ? "1" : ""); } catch (_) { /* private mode */ }
    dockAria();
    requestAnimationFrame(redraw);
  };
  $("#ws-fold", root).onclick = () => setFold(!root.classList.contains("folded"));

  // the dock's width (panel UX, 2026-10-18): the divider on its left edge drags it, between a width the conversation
  // reads in and one that leaves the graph its room; arrows move it, Shift faster, Home/End to the ends; a drag past
  // the narrow end folds the dock, a drag on a folded one opens it; a double-click or ↺ goes back to the screen's
  // default. Kept per browser like the fold. While dragging, the graph is held: its SVG scales, one layout follows.
  const DOCK_MIN = 300, DOCK_MAX = 720, GRAPH_MIN = 420, FOLD_AT = 220;
  const split = $("#ws-split", root), dockReset = $("#ws-dock-reset", root);
  let dockW = null;  // the person's width (px), or null: the screen's default (CSS)
  try { dockW = +localStorage.getItem(`${key}.dockw`) || null; } catch (_) { /* private mode */ }
  const dockDefault = () => parseFloat(getComputedStyle(root).getPropertyValue("--dock-def")) || 384;
  const dockMax = () => Math.max(DOCK_MIN, Math.min(DOCK_MAX, root.clientWidth - (parseFloat(getComputedStyle(root).getPropertyValue("--bar-w")) || 64) - GRAPH_MIN));
  const clampDock = (w) => Math.round(Math.min(dockMax(), Math.max(DOCK_MIN, w)));
  function dockAria() {
    const folded = root.classList.contains("folded"), w = folded ? 0 : dockW == null ? dockDefault() : clampDock(dockW);
    split.setAttribute("aria-valuemin", "0");
    split.setAttribute("aria-valuemax", String(dockMax()));
    split.setAttribute("aria-valuenow", String(w));
    split.setAttribute("aria-valuetext", folded ? "Thu gọn" : `${w} điểm ảnh`);
    dockReset.hidden = folded || dockW == null;
  }
  const setDock = (w, keep = true) => {  // the width asked for is kept; what shows is clamped to this window
    dockW = w == null ? null : Math.round(Math.min(DOCK_MAX, Math.max(DOCK_MIN, w)));
    if (dockW == null) root.style.removeProperty("--dock-pick"); else root.style.setProperty("--dock-pick", `${clampDock(dockW)}px`);
    if (keep) try { if (dockW == null) localStorage.removeItem(`${key}.dockw`); else localStorage.setItem(`${key}.dockw`, String(dockW)); } catch (_) { /* private mode */ }
    dockAria();
  };
  setDock(dockW, false);
  dockReset.onclick = () => { setDock(null); requestAnimationFrame(redraw); split.focus(); };
  split.ondblclick = () => { if (root.classList.contains("folded")) setFold(false); setDock(null); };
  split.addEventListener("keydown", (e) => {
    const step = e.shiftKey ? 64 : 16, now = dockW == null ? dockDefault() : clampDock(dockW);
    const to = {ArrowLeft: now + step, ArrowRight: now - step, Home: DOCK_MIN, End: dockMax()}[e.key];
    if (to == null && e.key !== "Enter") return;
    e.preventDefault();
    if (e.key === "Enter") { setFold(!root.classList.contains("folded")); return; }
    if (root.classList.contains("folded")) setFold(false);
    setDock(to);
  });
  split.addEventListener("pointerdown", (e) => {
    if (e.button !== 0) return;
    e.preventDefault();
    split.setPointerCapture(e.pointerId);
    const right = root.getBoundingClientRect().right, was = dockW, wasFolded = root.classList.contains("folded");
    let want = null, frame = 0;
    // the graph stays the picture it was, scaled on the compositor: a re-rasterised SVG per frame was the drag's cost
    const box0 = canvas.getBoundingClientRect(), dock0 = $(".ws-dock", root).getBoundingClientRect().width;
    const layers = [...canvas.querySelectorAll(".ws-svg, .ws-fxsvg")];
    for (const el of layers) { el.style.width = `${box0.width}px`; el.style.height = `${box0.height}px`; }
    // the conversation keeps its width while the pointer moves and reflows once it rests (a long one reflowed per frame
    // was ~60 ms a frame); the dock's edge and the divider follow the pointer every frame
    const panes = [...$(".ws-dock", root).querySelectorAll(".ws-pane")];
    let frozen = false, rest = 0;
    const freeze = (on) => { frozen = on; for (const el of panes) el.style.width = on ? `${el.getBoundingClientRect().width}px` : ""; };
    hold(true);
    root.classList.add("resizing");
    const paint = () => {
      frame = 0;
      const fold = want < FOLD_AT;
      root.classList.toggle("fold-intent", fold);
      if (fold) return;
      if (root.classList.contains("folded")) root.classList.remove("folded");
      if (!frozen) freeze(true);
      clearTimeout(rest);
      rest = setTimeout(() => freeze(false), 120);
      setDock(want, false);
      const w = box0.width + dock0 - clampDock(want), k = Math.min(1, w / box0.width);  // the graph's new room
      for (const el of layers) el.style.transform = `translate(${((w - box0.width * k) / 2).toFixed(1)}px, ${((box0.height * (1 - k)) / 2).toFixed(1)}px) scale(${k.toFixed(4)})`;
    };
    const move = (ev) => { want = right - ev.clientX; if (!frame) frame = requestAnimationFrame(paint); };
    const end = (ev) => {
      split.removeEventListener("pointermove", move);
      split.removeEventListener("pointerup", end);
      split.removeEventListener("pointercancel", end);
      if (frame) cancelAnimationFrame(frame);
      root.classList.remove("resizing", "fold-intent");
      for (const el of layers) { el.style.width = ""; el.style.height = ""; el.style.transform = ""; }
      clearTimeout(rest);
      freeze(false);
      if (ev.type === "pointercancel" || want == null) {  // nothing moved, or the drag was taken away: as it was
        setDock(was, false);
        root.classList.toggle("folded", wasFolded);
      } else if (want < FOLD_AT) {
        setDock(was, false);
        setFold(true);
      } else {
        setDock(clampDock(want));
        if (wasFolded) setFold(false);
      }
      hold(false);
    };
    split.addEventListener("pointermove", move);
    split.addEventListener("pointerup", end);
    split.addEventListener("pointercancel", end);
  });
  try { if (localStorage.getItem(`${key}.fold`)) { root.classList.add("folded"); $("#ws-fold", root).setAttribute("aria-expanded", "false"); dockAria(); } } catch (_) { /* private mode */ }
  return {
    setFold,
    /* the window changed: a kept width still leaves the centre its room */
    resize() { if (dockW != null) setDock(dockW, false); else dockAria(); },
  };
}
