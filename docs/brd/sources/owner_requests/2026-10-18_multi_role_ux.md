# OneWealth — Multi-Role UX Redesign & BRD Alignment (owner, 2026-10-18)

Verbatim, as given in the working session after the assistant's progress list shipped (2026-10-18), with the
sentence the owner added under it.

---

# OneWealth — Multi-Role UX Redesign & BRD Alignment

The Customer role has already received a graph-centric UI/UX redesign. Extend this redesign to **CIO, RM, Admin, and Expert**, giving each role a purpose-built experience without removing or weakening any existing functionality.

## 1. Audit Before Implementation

- Inspect the entire codebase, existing role-based routes, permissions, workflows, and current UI.
- Thoroughly review `docs/brd/`, including the original requirements, feature specifications, architecture, decisions, and existing UI/UX references.
- Identify the complete feature inventory and map each feature to its applicable roles.
- Update the BRD materials with role-specific UX concepts, navigation, workflows, visual references, and feature-to-UI mappings. Preserve the existing documentation structure and accumulate changes rather than replacing useful content.

## 2. Design Each Role for Its Actual Responsibilities

Treat the existing Customer graph-centric interface as a design reference, **not a template to copy blindly**.

- **CIO:** Prioritize market intelligence, portfolio-wide insights, risk exposure, scenario analysis, significant events, and decision support where supported by existing features.
- **RM:** Prioritize customer relationships, assigned portfolios, financial profiles, relevant news, customer needs, and follow-up actions where supported by existing features.
- **Admin:** Prioritize user and role management, configuration, integrations, operational health, and auditability where supported by existing features.
- **Expert:** Prioritize specialist analysis, research, financial interpretation, relevant evidence, and expert workflows where supported by existing features.

These are design hypotheses, not permission to invent capabilities. Verify each role's actual responsibilities and features against the BRD and implementation before finalizing its design.

## 3. Preserve All Original Functionality

**The BRD is the functional source of truth. This is a UI/UX redesign, not a feature-removal exercise.**

- Preserve all original features, business rules, data, workflows, permissions, and integrations.
- Reorganize how existing capabilities are presented and connected; do not silently delete, replace, or stub them.
- Keep role-specific access controls enforced by the existing authorization model.
- Maintain traceability from every original requirement to its redesigned interface and implementation.
- If a requirement is ambiguous, document the uncertainty rather than guessing.

## 4. Implement Incrementally

Start with **CIO**, unless the audit reveals a compelling dependency or implementation order.

For each role:

1. Document its original features and workflows.
2. Update the BRD with its proposed UX and relevant visual references.
3. Implement the redesigned interface using existing capabilities and shared design components where appropriate.
4. Test every original feature, navigation path, permission boundary, and important interaction.
5. Compare the implementation against the BRD and fix regressions before moving to the next role.

Keep the Customer experience working throughout. Reuse shared components where sensible, but do not force every role into the same graph layout or interaction model.

## 5. Completion Criteria

- Every role has a coherent, role-appropriate UX.
- Every original BRD feature remains available to its authorized users.
- The updated BRD accurately documents the design and implementation.
- Existing assistant capabilities, data flows, and integrations continue to work wherever applicable.
- Tests verify both feature preservation and role isolation.
- Report completed work, test results, remaining gaps, and the next role to implement.

Work autonomously and make sensible decisions. Do not stop after producing a plan or mockup: inspect, document, implement, and test each role end to end.

---

Each of role may have their agent llm design beneath, becareful not to break them with new design, and if possible, they should have their own assistant , too
