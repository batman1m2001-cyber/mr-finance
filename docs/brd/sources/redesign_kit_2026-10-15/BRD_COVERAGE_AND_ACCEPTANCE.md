# BRD Coverage & Acceptance Requirements

## Non-negotiable rule

The original BRD is authoritative for in-scope business requirements. Redesign must not silently remove, downgrade, hide beyond discoverability, or replace any required capability with a mockup.

BRD path:
`/home/thanglq/mr-finance/Đặc tả bộ agent tác động tin tức - Yêu cầu kinh doanh và nền tảng công nghệ.docx`

## Required workflow

1. Read the complete document, including tables, diagrams, appendices and embedded material where accessible.
2. Extract every requirement and assign stable IDs (e.g. BRD-FR-001, BRD-NFR-001, BRD-BR-001). Do not invent requirements to fill gaps.
3. Record exact source location/section/page where possible.
4. Map each requirement to:
   - business intent and expected behavior;
   - current implementation path and status;
   - target module/UI entry point;
   - API/model/service/agent dependencies;
   - acceptance test and verification evidence;
   - status: verified existing / needs refactor / new / partially supported / ambiguous / blocked.
5. Inventory existing product capabilities not in the BRD and preserve them unless a documented decision justifies a change.
6. Identify ambiguity, contradiction, dependencies, and missing decisions. Clearly separate documented requirement from proposed interpretation.
7. Update the matrix after implementation and regression testing.

## Completion criteria

- 100% of identified in-scope requirements are inventoried and traceable.
- No requirement is silently dropped.
- Every requirement has a status and verification approach.
- Every not-implemented/blocked requirement has an explicit reason and next step.
- UI consolidation preserves underlying capability and required behavior.
- A visible component is not evidence that the feature works; behavior must be tested.
- Existing capabilities changed or removed are listed with justification.
- Final report lists tests actually run and their results.

Do not claim 100% implementation completion if any requirement is blocked, partially implemented or unverified. Report traceability completeness separately from implementation completion.

## Suggested matrix columns

| ID | BRD source | Requirement | Type | Current code/path | Current status | Target implementation | UI entry point | Dependencies | Acceptance test | Evidence | Final status |
|---|---|---|---|---|---|---|---|---|---|---|---|

## Regression scope

Test core user journeys, data correctness, API contracts, authorization, error/empty/loading states, responsive behavior, graph interactions, assistant tool execution and any existing capability affected by the refactor.
