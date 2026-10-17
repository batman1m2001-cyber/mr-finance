# OneWealth — Assistant Sessions, Conversation History & Context Compaction (owner, 2026-10-17)

Verbatim, as given in the working session while the graph refinement was being built
([`2026-10-17_graph_dataflow_refinement.md`](2026-10-17_graph_dataflow_refinement.md)). It extends the assistant's
conversations and memory ([`2026-10-16_assistant_memory_agents.md`](2026-10-16_assistant_memory_agents.md), FEAT-37).

---

### Assistant Sessions, Conversation History & Context Compaction

Refactor the assistant from one endless conversation into a **session-based chat system inspired by Claude Code**.

- **Session management:** Allow users to create new sessions, switch between previous sessions, rename sessions, and delete/archive them. Automatically generate a concise, meaningful session title from the initial user request and refine it when more context becomes available.
- **Conversation persistence:** Persist each session's messages, timestamps, execution/tool activity, and relevant metadata. Restore the correct conversation when reopening a session or refreshing the application. Inspect the existing storage architecture before choosing or migrating the persistence layer; do not assume SQLite is appropriate without checking the current deployment model.
- **Two levels of memory:** Preserve the existing user-level global memory across sessions, while keeping each session's conversation history and working context isolated. Retrieve relevant global memories when needed, but never leak one user's data or unintentionally mix unrelated sessions.
- **Context compaction:** Implement automatic context management when approaching the model's context limit. Summarize older messages into a concise, structured continuation summary, preserve key decisions, user preferences, unresolved tasks, important entities, tool results, and references to persistent data, then continue with recent messages. Make compaction recoverable and avoid silently losing important information.
- **Session continuity:** Each session must retain its own goals, context summary, and relevant history. Starting a new session resets the active conversation context without erasing global memory or previous sessions.
- **UI integration:** Add a session switcher/history view and a prominent New Chat action within the existing OperonX Studio-style assistant panel. Keep the interface compact and consistent with the current OneWealth design.
- **Testing:** Verify persistence across refreshes, correct session isolation, title generation, compaction and continuation, tool-call recovery, and multi-user access controls.

Inspect the existing assistant, memory management, streaming, database, and authentication implementations first. Reuse existing infrastructure where appropriate, implement the complete feature, and update the BRD and tests accordingly. Do not replace the existing global memory system with per-session memory.
