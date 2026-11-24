/* The one place web/ reaches the backend (D8). Every route is under /api/ (and /samples/) on BASE: "" means the
   same origin that served this page. To serve web/ from somewhere else, set BASE to the backend's origin. */
export const BASE = "";

export function api(path, opts) {
  return fetch(BASE + path, opts);
}

/* The WebSocket address for a path on BASE (ws:// or wss:// to match). */
export function socket(path) {
  const url = new URL(BASE + path, location.href);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  return url.href;
}
