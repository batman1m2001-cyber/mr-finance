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
| [ADR-0012](ADR-0012-the-copilot-routes-and-never-reads-client-data.md) | The Copilot routes; it never reads client data | accepted (planned) | 2026-10-15 |
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
