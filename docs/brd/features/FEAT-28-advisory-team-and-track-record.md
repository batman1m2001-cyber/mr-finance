# FEAT-28 — Specialist team and advisory track record (mock)

| | |
|---|---|
| Type | Existing capability from PR #13 (2026-10-13); in no source document — kept by ADR-0003 |
| Requirements | None (see Q-19). Not BRD-BR-15 |
| Users | Client (their specialist), RM / staff (performance) |
| Entry points | [SCR-CL-07 Chuyên gia](../ux/screens/client.md#scr-cl-07--chuyên-gia-specialist-team), [SCR-RM-04](../ux/screens/rm.md#scr-rm-04--hiệu-quả-tư-vấn-of-one-client), [SCR-RM-05](../ux/screens/rm.md#scr-rm-05--hiệu-quả-tư-vấn-all-clients); `GET /api/advisory?client_id=`, `GET /api/advisory/all` |
| Status | see [traceability](../requirements/requirements_traceability.md) §3 |

## Behaviour
Reads `data/advisory.json` (mock, as of 2026-10-09, “Dữ liệu giả định cho demo”): per client a specialist
(name, contact, hours) and a tracking record (recommendations with outcome, money gained/lost, missed actions,
missed news, AI pipeline scores per stage, news-reading engagement). `/api/advisory/all` sums over clients. The
staff pages carry a “Nội bộ” banner.

## Implementation
`app/web.py` (`advisory`, `advisory_all`), `scripts/make_advisory.py`; UI `web/app.js` (tabs `rm`,
`performance`, `perfall`).

## Acceptance and tests
`tests/test_app.py::test_the_specialist_team_and_the_advisory_record`, `::test_the_advisory_record_over_every_client`.

## Limitations
Everything shown is invented; the page says it is illustrative and not accuracy tracking (Q-19); no entry is
dated after the data date since 2026-10-15 (DEF-05). It must not be presented
as accuracy tracking (FEAT-18).
