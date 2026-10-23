# Decisions (ADRs)

Why the product is the way it is. One file per decision, append-only: a changed decision gets a **new** ADR that
supersedes the old one (the old one is marked `superseded by ADR-nnnn`, never edited otherwise). Template:
[`../templates/decision_template.md`](../templates/decision_template.md).

| ADR | Decision | Status | Date |
|---|---|---|---|
| [ADR-0001](ADR-0001-keep-the-brd-file-out-of-the-public-repository.md) | Keep the BRD file out of the public repository | accepted | 2026-10-15 |
| [ADR-0002](ADR-0002-implement-the-brd-on-operonx-not-the-brd-stack.md) | Implement the BRD on operonx, not on the BRD's stack | accepted | 2026-10-15 |
| [ADR-0003](ADR-0003-keep-the-capabilities-that-predate-the-brd.md) | Keep the capabilities that predate the BRD | accepted | 2026-10-15 |
| [ADR-0004](ADR-0004-assumed-factor-model-parameters.md) | Assumed factor-model parameters, labelled “giả định” | accepted | 2026-10-15 |
| [ADR-0005](ADR-0005-mock-clients-and-prices-public-news.md) | Mock clients and prices, public news, a mock restricted list | accepted | 2026-10-09 (data), 2026-10-15 (news) |
| [ADR-0006](ADR-0006-the-role-switcher-is-not-security.md) | The role switcher is a demo, not security | superseded by ADR-0020 | 2026-10-15 |
| [ADR-0007](ADR-0007-policy-cost-alerts-stay-outside-the-engine.md) | Policy-cost alerts stay outside the scenario engine | accepted (partly implemented) | 2026-10-15 |
| [ADR-0008](ADR-0008-the-client-sees-asset-classes-only.md) | The client sees effective results at asset-class level only | accepted | 2026-10-15 |
| [ADR-0009](ADR-0009-ai-barrier-by-graph-inputs-in-one-process.md) | The AI barrier is enforced by graph inputs, in one process | superseded in part (ADR-0022) | 2026-10-15 |
| [ADR-0010](ADR-0010-two-configured-models-and-a-labelled-mock.md) | Two configured models, refused if equal; a labelled mock | accepted | 2026-10-15 |
| [ADR-0011](ADR-0011-engine-in-floats-rounded-to-the-dong.md) | The engine computes in floats and rounds to the dong once | accepted | 2026-10-15 |
| [ADR-0012](ADR-0012-the-copilot-routes-and-never-reads-client-data.md) | The Copilot routes; it never reads client data | accepted, amended by ADR-0026 | 2026-10-15 |
| [ADR-0013](ADR-0013-wrap-the-legacy-pages-in-the-new-shell.md) | Wrap the legacy pages in the new shell instead of rewriting them | superseded by ADR-0019 | 2026-10-15 |
| [ADR-0014](ADR-0014-docs-brd-is-the-living-product-repository.md) | docs/brd is the living product knowledge repository | accepted | 2026-10-15 |
| [ADR-0015](ADR-0015-decisions-of-the-first-build-plan.md) | Decisions of the first build plan (D1–D9) | accepted | 2026-10-09 |
| [ADR-0016](ADR-0016-configuration-two-person-rule.md) | Configuration is versioned; two people for the factor model, thresholds and restricted list | accepted | 2026-10-16 |
| [ADR-0017](ADR-0017-goal-impact-rule.md) | Goal impact (FR-404): goals draw on financial assets in date order; levels as in goals planning | accepted | 2026-10-16 |
| [ADR-0018](ADR-0018-owner-decisions-public-quotes-and-ai-in-the-demo.md) | Owner decisions: BRD quotes stay public; the demo may send client text to the model | accepted | 2026-10-16 |
| [ADR-0019](ADR-0019-every-page-is-a-module-page.md) | Every page is a module page; the pre-redesign pages are rebuilt and removed | accepted | 2026-10-16 |
| [ADR-0020](ADR-0020-sign-in-with-own-accounts.md) | Everyone signs in with their own account; the role switcher is gone | accepted | 2026-10-16 |
| [ADR-0021](ADR-0021-market-data-through-scheduled-jobs.md) | Market data comes from public sources through scheduled jobs into SQLite | accepted | 2026-10-16 |
| [ADR-0022](ADR-0022-the-ai-zone-is-a-second-process.md) | The AI zone is a second process with its own database, reaching the bank through a signed inbox | accepted | 2026-10-16 |
| [ADR-0023](ADR-0023-client-data-barrier-by-configuration.md) | The client-data barrier is one guard on every model call, set by configuration (`client_ai`) | accepted | 2026-10-16 |
| [ADR-0024](ADR-0024-encryption-at-rest-secrets-and-headers.md) | Client data sealed per column (AES-256-GCM, rotating keys), keys from a secret store, every response hardened | accepted | 2026-10-16 |
| [ADR-0025](ADR-0025-postgresql-export-and-worm-audit.md) | The move to the bank proven by a checked PostgreSQL export; the audit log on write-once segments | accepted | 2026-10-16 |
| [ADR-0026](ADR-0026-the-assistant-reads-client-data-only-where-client-ai-allows.md) | The assistant's model reads client data only where `client_ai` allows it; template mode otherwise (amends ADR-0012) | accepted | 2026-10-16 |
| [ADR-0027](ADR-0027-conversations-in-their-own-sqlite-wal-file.md) | Conversations and memory in their own SQLite file in WAL mode, chosen by measurement | accepted | 2026-10-16 |
| [ADR-0028](ADR-0028-three-memory-layers.md) | Three memory layers: the conversation, a few sourced long-term items, the archive | accepted | 2026-10-16 |
| [ADR-0029](ADR-0029-knowledge-base-on-operonx-kb.md) | The knowledge base on operonx-kb, product and personal collections apart | accepted | 2026-10-16 |
| [ADR-0030](ADR-0030-web-search-through-openrouter.md) | Web search through the existing OpenRouter key, the query scrubbed, results cited and not stored | accepted | 2026-10-16 |
| [ADR-0031](ADR-0031-two-new-agents-only.md) | Two new background agents only: the memory consolidator and the follow-up watcher | accepted | 2026-10-16 |
| [ADR-0032](ADR-0032-one-tool-registry.md) | One tool registry: roles, writes confirmed and verified, timeouts, costs | accepted | 2026-10-16 |
| [ADR-0033](ADR-0033-the-ecosystem-map-on-the-agent-page.md) | The Agent Ecosystem Map lives on the Agent page, drawn from real records | accepted | 2026-10-16 |
| [ADR-0034](ADR-0034-readiness-by-an-eval-gate-on-real-models.md) | Readiness is an eval gate on real models, with measured costs | accepted | 2026-10-16 |
| [ADR-0035](ADR-0035-the-customer-workspace-is-one-persistent-graph.md) | The Customer's workspace is one persistent graph; pages become lenses and sheets | accepted (experiment); §1 superseded by ADR-0036 for staff; the graph hidden from the client by ADR-0037 | 2026-10-17 |
| [ADR-0036](ADR-0036-every-staff-role-works-at-its-own-desk.md) | Every staff role works at its own desk, in the Customer workspace's frame | accepted (experiment) | 2026-10-18 |
| [ADR-0037](ADR-0037-the-clients-four-sections-carry-the-banks-names.md) | The client's four sections carry the bank's names; the graph is hidden from the client | accepted | 2026-10-22 |
| [ADR-0038](ADR-0038-a-second-client-set-the-santander-vn-private-book.md) | A second client set: a Private book converted from Santander's public data; the demo stays (keeps ADR-0005) | proposed | 2026-10-23 |
