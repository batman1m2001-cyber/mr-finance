# FEAT-16 — Policy agent and policy radar

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-FR-306, BRD-RULE-AI-01 (owner Compliance, risk medium; sees no portfolio, draws no conclusion for a family), BRD-RULE-AI-02 (its prompt is versioned configuration), BRD-RULE-SEC-04 (the verifier is not the person who added the document) |
| Users | Compliance (owner: adds, verifies, updates, runs the agent), CIO (reads) |
| Entry points | [SCR-CMP-05](../ux/screens/compliance.md) “Chính sách” (Compliance `#/compliance/chinh-sach`, CIO `#/cio/chinh-sach`); `GET /api/policy[/{id}]`, `POST /api/policy`, `/api/policy/verify`, `/api/policy/status`, `/api/policy/summarise` |
| Screenshots | [the radar](../assets/current_ui/SCR-CMP-05_desktop-light.jpg) · [a quote marked in the document](../assets/current_ui/FEAT-16-quote_desktop-light.jpg) |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
Compliance follows the public policy documents that matter to the bank's advice, and reads an internal summary of
each in which every point is backed by the document's own words.

## Documents (`src/policy/source.py`, `store.py`; table `policy_documents`)
- **From the Official Gazette** (`https://congbao.chinhphu.vn/van-ban/…`): the server reads the page, takes the
  signed PDF it links on the gazette's own file host (`congbaocdn.chinhphu.vn`; any other link is ignored), extracts
  the text with pypdf and keeps the PDF's SHA-256, the title, number, issuer (from the number's suffix) and issue
  date. A PDF without a text layer is refused with the reason.
- **From another official page** (a draft under consultation): the address must be https on an official domain
  (chinhphu.vn, sbv.gov.vn, mof.gov.vn, ssc.gov.vn, quochoi.vn, vbpl.vn, moj.gov.vn, mpi.gov.vn, gso.gov.vn); the
  text is pasted, or left empty while it is not published.
- **Verified** by a second Compliance person — never the one who added it — with a note of at least 20 characters;
  the text's hash at that moment is kept. The agent reads only verified documents whose text still has that hash.
- **Where it stands**: Dự thảo → Lấy ý kiến → Đã ban hành → Có hiệu lực, or Dừng / bãi bỏ, each change with the
  date it happened and a note naming the source of the information (at least 10 characters).
- Adding, verifying, each status change and each summary are audit rows (`policy.add`, `.verify`, `.status`,
  `.summary`).

## The agent (`src/policy/agent.py`, `text.py`)
- Reads the verified document's title, number, issuer and text — nothing else; the module imports no client,
  family or portfolio data, and a test checks that no client name or id reaches the model.
- Answers `{summary, points: [{point, article, quote}]}`, 2–6 points. **Every quote is checked word for word**
  against the document (Unicode NFC, white space collapsed so a PDF line break does not fail a faithful quote) and
  must lie **inside the article it names** (the document split at its “Điều N.” headings). No recommendation wording
  (Compliance's `forbidden_phrases`), no conclusion for a client, family or portfolio.
- A failing answer goes back to the model with what failed, at most twice; then the run is an error (an `agent`
  alert, key `policy`). Each attempt is a node of an agent run (agent `policy`), with the prompt, model, tokens and
  findings, counted against the daily token budget.
- **Live**: `llm:cio` (the BRD names the same model family as the CIO agent's, at a lower effort) with the `policy`
  prompt of the prompts configuration (a version kept before F9 has none; the default is used and the version id
  recorded). **Mock**: the first sentence of each of the first articles, quoted as it stands, labelled “Mô phỏng —
  không gọi mô hình”. In inbox mode only mock runs at the bank.
- The summary is internal: shown to Compliance and the CIO, never to clients.

## The radar (F-D8 — our reading, labelled “Đề xuất”)
The BRD names “radar chính sách” without describing it (Q-09). Here it is: every tracked document by its last
change, its status path (e.g. “Đã ban hành → Có hiệu lực”), whether its source is verified and summarised, counts
by status, and what is **new or changed since the reader last looked** (the last look is kept in the reader's
browser). Labelled “Đề xuất” until the owner defines it.

## The BRD's data model
`policy_documents` is built. `policy_matches` (a document matched to families) is not: matching regulations to
families' goals is the goal branch's job ([FEAT-10](FEAT-10-goal-branch.md)), and the policy agent by rule draws no
conclusion for a family.

## Tests
`tests/test_policy.py`; the catalogue entry in `tests/test_catalogue.py`.
