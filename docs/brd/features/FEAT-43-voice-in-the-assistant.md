# FEAT-43 — Talking to the assistant (voice)

| | |
|---|---|
| Type | Extension (owner request, 2026-10-26) |
| Requirements | the owner's brief ([VOICE_PLAN appendix](../../VOICE_PLAN.md#appendix--the-owners-brief-2026-10-26)) |
| Users | anyone signed in, in every role's assistant panel; the iPhone app (1.2.0) asks for the microphone once |
| Entry points | the panel's microphone button; `WS /api/assistant/voice?rate=` (`assistant_voice_flow`, `src/voice/`) |
| Plan | [docs/VOICE_PLAN.md](../../VOICE_PLAN.md) P1–P4 |
| Status | built (2026-10-27) |

## Purpose

Older clients ask by speaking and hear the answer read to them at their pace, while the panel shows it as usual.

## Behaviour

1. **Listen.** The microphone button opens the socket (sign-in and the page's own `Origin` checked); the bar says
   *Mời bạn nói…*. The browser streams 16-bit PCM; the callbot's VAD (Silero) cuts utterances, STT turns each into
   words shown as the caption.
2. **Ask.** After 1.2 s of quiet (`VOICE_SILENCE_MS`, 600–4000) the words are the question: the panel sends it as a
   typed one would (`POST /api/assistant/stream`) with `voice: true`, which only adds a rule for answers read aloud.
   The microphone is shut while the assistant thinks and speaks (half duplex).
3. **Speak.** The answer's words are cut into sentences (never inside a number or a date; markdown read as prose),
   each synthesised (ZipVoice) and played as soon as it is ready; **Dừng** stops at once. After the last sentence
   the microphone listens again. Nothing is said unprompted.
4. **Typed turns are unchanged**: without `voice: true` the turn is the same request as before.

## Measured

See [VOICE_PLAN §4](../../VOICE_PLAN.md#4-measured-2026-10-27): asked 1.18 s after the person stops; one sentence
synthesised in 0.1–0.2 s; the transcript as said.
