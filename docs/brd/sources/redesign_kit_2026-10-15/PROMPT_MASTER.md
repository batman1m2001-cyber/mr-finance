# OneWealth — Complete Redesign, BRD-Driven Refactoring & Financial Intelligence Experience

You are working directly in the existing OneWealth / Mr.Finance repository. Your task is to improve the real application, not merely produce a mockup or design proposal.

Primary BRD:
`/home/thanglq/mr-finance/Đặc tả bộ agent tác động tin tức - Yêu cầu kinh doanh và nền tảng công nghệ.docx`

Reference images in the supplied kit:
- `assets/current_dashboard_reference.png`: current UI to improve.
- `assets/onewealth_redesign_concept_board.png`: broad visual direction only. It is an illustrative concept board, not a pixel-perfect specification, not a source of truth, and not real financial data.

## Mission

Evolve OneWealth from a collection of dashboard cards into a coherent, polished financial-intelligence product. The experience should be calm, clear, visually informative, and easy to navigate. Connect relevant features through a shared, evidence-based financial context while preserving every in-scope BRD capability and existing working feature.

Do not stop at recommendations. Inspect the repository, establish a plan, implement a sensible first complete slice, run checks, and report verified results.

## 1. Inspect before changing anything

- Inspect repository structure, framework, dependencies, current routes/pages, components, API contracts, data models, agent workflows, authentication/authorization, tests, and run instructions.
- Read the complete BRD, including tables, diagrams, appendices, and embedded content where available. Use the document itself as the primary requirements source.
- Identify existing functionality not explicitly covered by the BRD and preserve it unless removal is justified and documented.
- Separate verified facts, explicit requirements, assumptions, recommendations, and unresolved questions.
- Do not invent code behavior, product capabilities, data, integrations, financial figures, or test results.

Before major changes, create a concise implementation plan and a requirement-to-code traceability inventory. Continue with implementation when there is enough information; ask only if a genuinely blocking business decision cannot be resolved responsibly.

## 2. Redesign the UI/UX

The current dashboard is cleaner than before but remains too card-oriented, static, and fragmented. Reduce scattered information and repetitive text while retaining meaningful detail.

Design principles:
- Less redundant text; more information communicated visually.
- Strong hierarchy: users should understand their financial state, important changes, and items needing attention within seconds.
- Calm, restrained styling; avoid excessive gradients, saturated colors, shadows, neon, decoration, and gratuitous motion.
- Clear typography, consistent spacing, good contrast, accessible controls, responsive layouts, and predictable interactions.
- Progressive disclosure: concise summaries first; detailed data, evidence, and metadata remain accessible on demand.
- Avoid giant empty panels, unnecessary cards, and oversized whitespace that wastes useful space.
- Keep real data and working interactions. Do not replace functioning features with static mockups or decorative buttons.

Explore a dashboard structure such as:
1. Financial Pulse — net worth, meaningful changes, liquidity and key signals.
2. Wealth & Money Flow — portfolio distribution and, where supported, income/expense/savings/investment flows.
3. Intelligence & Attention — prioritized news impacts, risk changes, alerts and goal implications.

Treat this as a hypothesis to validate against the actual application and BRD, not a reason to force every page into the same layout.

## 3. Financial Intelligence Graph and meaningful visualization

Explore a unified domain graph connecting supported entities such as assets, asset classes, financial institutions/data sources, cash flows, goals/scenarios, news events, companies/industries, risk exposures, alerts, and analysis evidence.

Do not force a simple tree if relationships are many-to-many. A graph can support hierarchical navigation, filtering, grouping, drill-down, and contextual details. Build only relationships grounded in real data, verified logic, or explicit BRD requirements. Do not imply causation when evidence supports only correlation or potential impact.

Create a coherent visual anchor, choosing the right visualization for the task:
- Sankey diagram for aggregated money flows where the data supports it.
- Treemap or allocation chart for wealth composition.
- Interactive relationship graph for news → affected entities → portfolio exposure → risk/goals, where supported.
- Timeline for events and changes.
- Scenario comparisons for explicit hypothetical assumptions.

Do not put every visualization on every screen. Avoid unreadable hairballs: use aggregation, filters, progressive disclosure, semantic zoom, and contextual detail panels.

Motion should communicate direction, magnitude, change, or relationship. Use restrained flow animation, subtle path/node highlighting, and smooth transitions only where useful. Respect reduced-motion settings and offer a static alternative. Never animate every element continuously or sacrifice readability/performance.

## 4. Add OneWealth Copilot as a first-class interface

Explore a persistent but unobtrusive assistant icon that opens a side panel without navigating away from the current page. It should be context-aware and use only authorized data and real application capabilities.

Expected capability categories, subject to the BRD and verified implementation:
- Ask: answer questions using authorized application data, with timestamps and source references.
- Investigate: explain supported relationships among news, assets, exposure, risk and goals.
- Analyze: invoke real analytical capabilities and communicate assumptions, evidence, uncertainty and limitations.
- Act: execute supported tasks through actual tool/API contracts, with input validation, authorization, confirmation when appropriate, progress/error states, and truthful results.
- Navigate: link to relevant entities, pages, graph nodes and visualizations.
- Continue: retain useful conversation/task context within applicable security and data-retention rules.

Do not implement a superficial chatbot with hardcoded answers. Do not duplicate business logic inside the assistant. Do not claim a task was completed when it was only suggested or drafted. Unsupported capabilities must be explicitly identified. Consequential actions require appropriate safeguards; never bypass the product's existing permissions.

See `PROMPT_ONEWEALTH_COPILOT.md` for additional requirements.

## 5. BRD completeness is mandatory

The original BRD is the authoritative source for required business capabilities. Redesign/refactoring must never be used as a reason to omit, simplify away, or silently remove a required feature.

- Extract every functional requirement, business rule, user workflow, integration requirement, constraint and relevant non-functional requirement.
- Assign stable requirement IDs and map each to existing implementation, target implementation, UI entry point, dependencies and verification criteria.
- Preserve existing capabilities outside the BRD unless removal is explicitly justified.
- UI consolidation is allowed only if underlying capability and required behavior remain available.
- Do not treat a screen/component as proof that a feature works.
- If something is blocked by missing decisions, credentials, services or infrastructure, mark it blocked and explain why.
- Do not invent missing requirements. Record ambiguity and distinguish proposed interpretation from documented requirement.

See `BRD_COVERAGE_AND_ACCEPTANCE.md`. Maintain the traceability matrix as implementation changes.

## 6. Refactor the codebase responsibly

Review frontend architecture, shared design system, domain models, API contracts, backend services, data ingestion, agent orchestration, provider abstractions, persistence/caching, configuration, logging, error handling, tests and deployment workflow as applicable.

- Separate presentation, business logic, data access and agent orchestration.
- Reuse existing components and services when sound.
- Introduce new services, abstractions, frameworks, graph databases or visualization engines only when there is a demonstrated need.
- Keep API contracts and frontend assumptions consistent.
- Preserve source references, timestamps, evidence and uncertainty where supported.
- Keep secrets out of source code.
- Avoid unrelated rewrites, dependency upgrades and speculative architecture.
- Maintain compatibility with the documented development workflow.

## 7. Deliverables

Create or update documentation in the repository, following its conventions:
1. Current-state architecture and observed problems.
2. BRD requirement inventory and traceability matrix.
3. Proposed target architecture with rationale.
4. UI information architecture and redesign notes.
5. Implementation plan prioritized by value, dependency and risk.
6. Test/acceptance plan.
7. Final coverage, regression and known-blocker report.

Implement the redesign and prioritized changes. Do not stop after writing the plan. Work in small, verifiable stages and keep the application runnable.

## 8. Verification and completion report

Run relevant available tests, linting, formatting, type checks, build/startup checks, API/data-contract validation and critical user-flow checks. Verify business logic as well as presentation. Do not report a check as passed unless it was actually executed.

Final report must distinguish:
- Implemented and verified.
- Implemented but not fully verified.
- Partially implemented.
- Blocked/not implemented, with reasons.
- Regressions found and their status.
- Tests/checks actually executed and their outcomes.
- Any requirement or existing capability changed/removed, with justification.

The acceptance standard is 100% requirement traceability and no silently dropped in-scope requirement. This does not permit claiming 100% implementation completion while blockers remain.

## Working style

Be pragmatic and direct. Make ordinary design/engineering decisions without asking for unnecessary approval, and document them. Prioritize clarity, usefulness, evidence, correctness and maintainability over novelty.

The goal is a complete, coherent improvement to OneWealth: an elegant financial-intelligence experience, an evidence-based connected view of the user's financial context, and a maintainable codebase aligned with the full original BRD.

Let's get started.
