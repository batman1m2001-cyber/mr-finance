# OneWealth — Living Interface & Smart Animations

I want to make OneWealth feel like a living, intelligent system that interacts naturally with users, especially when they chat with the AI assistant.

First, inspect the existing codebase, assistant lifecycle, design system, and `docs/brd/`. Then implement this as an incremental enhancement without disrupting existing functionality.

### 1. Create a Living Experience

Make the interface respond subtly to user interactions and assistant activity:

- **Idle:** Subtle ambient motion around the assistant to create a sense of presence.
- **Thinking:** Gentle pulses or flowing highlights while the assistant is processing a request or executing tools.
- **Responding:** Briefly highlight relevant charts, assets, news, or graph connections when the assistant references them.
- **Completed / Error:** Provide clear, elegant visual feedback.

Explore subtle light waves, contextual highlights, flowing connections, and smooth transitions. Make the page feel interconnected, as if the assistant is interacting with the wider application, rather than animating an isolated chat panel.

Keep the aesthetic premium, minimal, and calm. Avoid excessive glowing effects, distracting movement, heavy 3D, or continuously animating the entire page. **Motion should communicate meaningful state changes, not exist merely for decoration.**

### 2. Performance Is Non-Negotiable

- Prefer lightweight CSS transitions, transforms, opacity, and simple SVG effects.
- Avoid unnecessary re-renders, expensive layout recalculations, heavy animation libraries, and continuous JavaScript loops.
- Drive animations from actual assistant states and application events; never fabricate progress.
- Suspend nonessential animations when the tab is hidden or the relevant interface is inactive.
- Respect `prefers-reduced-motion` and keep the application usable on low-end devices.
- Measure performance before and after implementation. Simplify any effect that noticeably degrades responsiveness.

### 3. Preserve and Update the Existing Product

- Do not redesign the entire application or alter existing business logic unnecessarily.
- Preserve every existing feature and requirement documented in `docs/brd/`.
- Update the relevant feature specifications, UX documentation, design system, traceability records, and changelog to include this new capability.
- Reuse the existing architecture and dependencies wherever possible.

### 4. Implement and Verify

Do not stop at proposing ideas. Implement the most valuable effects, test the assistant interaction lifecycle and existing user workflows, and run available checks.

Report the actual changes, test results, performance observations, and any remaining limitations.

**The goal: OneWealth should feel alive because it responds intelligently to the user—not because every pixel is constantly moving.**
