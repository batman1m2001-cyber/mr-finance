# ADR-0019 — Every page is a module page; the pre-redesign pages are rebuilt and removed

- **Status:** accepted (supersedes [ADR-0013](ADR-0013-wrap-the-legacy-pages-in-the-new-shell.md))
- **Date:** 2026-10-16
- **Sources:** owner request 2026-10-16 (OWN-UI-02, `sources/owner_requests/2026-10-16_ui_redesign.md`);
  `docs/UI_REDESIGN_PLAN.md` R3 (gaps G1, G7)

## Context

ADR-0013 kept the eight pre-BRD pages (`web/app.js`, tabs overview, sources, scenarios, risk, alerts, rm,
performance, perfall) inside the new shell unchanged. The owner asked for every page in the concept board's look;
two visual generations, two CSS files with clashing class names and a `window.Legacy` bridge were the cost.

## Decision

- Each pre-redesign tab is an ES module in `web/pages/`: Chi tiết `detail.js`, Tài sản `holdings.js`, Kế hoạch
  `plan.js`, Khẩu vị rủi ro `risktest.js`, Chi phí chính sách `policy.js`, Chuyên gia / Duyệt đề xuất `advisor.js`,
  Hiệu quả tư vấn `performance.js` and `perfall.js`. Every block and action of the old tab is kept; the services are
  unchanged.
- `web/app.js`, `web/app.css`, `web/charts.js` and `web/fmt.js` are deleted. The base rules the pages need are in
  `web/core/tokens.css`; the old charts live on in `web/charts/money.js`.
- The shell owns the client picker (remembered in `localStorage` `mf.client`), the personal / family scope and
  “Làm lại demo” (server reset, the followed goals and the tab's kept reads cleared, then a reload).
- Pages render into `#page`. Each route renders into its own new element inside it, so a page still drawing for an
  earlier route writes into a detached node, never into the page shown now.
- The UI's files are served with `Cache-Control: no-cache` (revalidated with their ETag), so a browser never runs a
  module from before a deploy beside one from after it.

## Consequences

- One visual generation; `tests/test_web.py::test_every_page_is_a_module_page` keeps it so.
- What a page keeps for the browser tab (the last statement read, the chat, the risk-test answers so far) is per page
  module, not one shared state object.
