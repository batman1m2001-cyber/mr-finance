# OneWealth — Talking to the assistant: plan

**Status: done** (owner's go, 2026-10-26; P1–P4 built and measured 2026-10-27, on :8030 with the iPhone app 1.2.0 —
the owner's "go with voice plan … sync the iphone app" took it live). Feature: [FEAT-43](brd/features/FEAT-43-voice-in-the-assistant.md). The brief is kept in the [appendix](#appendix--the-owners-brief-2026-10-26).

## 1. What exists

| Piece | Where | What it does |
|---|---|---|
| VAD | callbot `src/call/vad/_pool.py` (staging 229ba89) | `VadState.push(pcm_int16, t)`: resample to 16 kHz (soxr), bandpass + spectral gating + AGC, Silero ONNX, the segment state machine (start at p ≥ 0.5, end after 500 ms below 0.35, 500 ms pre-roll, 45 s cap). Returns finished utterances. `VadPool` runs it off the event loop; `audio_worker:` in resources.yaml |
| STT | callbot `src/call/stt/ops.py` | `STTOp(resource="stt")`: one utterance → its transcript, KServe v2 binary request to `http:stt` |
| TTS | callbot `src/call/tts/ops.py` | `TTSOp._synth_one`: one sentence → a WAV from ZipVoice (`http:tts`), lead/trail silence trimmed to 50/80 ms |
| `http:` resources | callbot `src/call/_endpoints.py` | `HttpEndpointConfig` → `HttpEndpoint` (url, key header, timeout, options) |
| Assistant turn | `src/assistant/ops.py` `stream_turn`, `POST /api/assistant/stream` | The turn as events: step, text (the model's words as they come), wait, answer |
| Panel | `web/copilot.js` `send(q)` → `streamed()` | Draws the turn live, keeps the conversation, the confirmations, the graph events |

`http:stt` and `http:tts` are already declared in `resources.yaml` (copied from the callbot).

## 2. Design

VAD is already the streaming on the way in (it hands over each finished utterance), and TTS per sentence is the
streaming on the way out. Nothing new is invented between them: **the voice door only hears and speaks; the question
goes through the panel's `send(q)`**, so a spoken question is the same turn as a typed one — the same events, the
same conversation, the same confirmations (a write is still confirmed by a button, never by voice).

```
mic (PCM16, browser rate) ──ws──► vad_stream ──utterance──► STTOp ──► end_of_turn ──{"asked": text}──► panel send(q)
                                                         └─► {"heard": text} (live caption)
panel: the turn's "text" events / the answer ──ws {"say"}──► sentences ──► tts_sentence ──{"voice": wav}──► play queue
```

One websocket, `GET /api/assistant/voice` on :8030, graph `assistant_voice_flow`, one run per open microphone.

| # | Decision | Why |
|---|---|---|
| V-D1 | **Lift** the callbot's `_pool.py` + `_energy_trim.py`, the STT op and `_synth_one` + trim into `src/voice/`, unchanged except the import paths, the input rate (a per-state setting, not the 8 kHz class constant) and thread mode only | The brief: reuse, don't rebuild. mr-finance cannot import the callbot (separate repo, not a package). One server process holds a handful of microphones, so the process-mode pool is not needed |
| V-D2 | The browser sends its native rate (usually 48 kHz) and VAD's soxr resamples | Firefox refuses a 16 kHz `AudioContext` on a microphone; the resampler is already in `VadState` |
| V-D3 | **End of turn**: each transcript is added to the turn's text; the turn is asked when nothing has been voiced for `VOICE_SILENCE_MS` (default **1200 ms**, from `.env`), VAD is not inside an utterance, and no utterance is still at STT | The brief's 1 s example, plus 200 ms: older speakers pause longer inside a sentence. Configurable, as asked. The "none at STT" check is what keeps a slow STT reply from splitting one question in two |
| V-D4 | **Speaking**: the panel forwards the turn's `text` events as they come (the model writing), or the answer's text when none came (template and fallback answers). The server cuts at `. ! ? ; :` followed by a space, and at line ends; markdown is read as prose (no `**`, `#`, list marks, table bars) | The first sentence is spoken while the model writes the second. `7,54` and `7.5` are not cut: a cut needs a space after the mark |
| V-D5 | TTS at **speed 1.0** (server default 1.2), no lower-casing, no "/"→space | Measured 2026-10-26 (scratchpad probe): 1.2 = 4.01 s, 1.0 = 4.88 s clean, 0.9 = 5.38 s with a glassy onset. ZipVoice already reads "7,54 tỷ đồng", "(54%)", "09/10/2026" correctly; the callbot's normaliser would break the date |
| V-D6 | **Half duplex, the person leads**: the microphone is paused while the assistant thinks and speaks and opens again after the last sentence plays; a big **Dừng** stops the speech at once (and the server stops synthesising). Nothing is said unprompted: no "are you still there", no timeout | Elderly users read their numbers and fortunes at their pace and ask the next question when ready. No echo of the assistant's voice reaching its own ears |
| V-D7 | Sign-in is checked when the socket opens (the cookie rides the handshake); the `Origin` must be the page's host. `permissions-policy` allows `microphone=(self)` | The voice door costs STT/TTS calls and reads nothing without the person's own turn behind it |

Protocol (JSON text frames, PCM as binary frames):

| Way | Frame | Meaning |
|---|---|---|
| → | binary | mic PCM16 mono at `?rate=` |
| → | `{"type":"say","turn":n,"text":…}` / `{"type":"say","turn":n,"end":true}` | words to speak / flush the rest |
| → | `{"type":"drop","turn":n}` | a tool step began: the unspoken lead-in is dropped |
| → | `{"type":"stop"}` | Dừng |
| ← | `{"type":"heard","text":…}` | one utterance's transcript (caption) |
| ← | `{"type":"asked","text":…}` | the turn's question: the panel sends it |
| ← | `{"type":"voice","turn":n,"text":…,"wav":base64,"ms":…}` | one sentence, ready to play |
| ← | `{"type":"spoken","turn":n}` | the last sentence of turn n has been sent |

## 3. Phases

| Phase | Work | Gate |
|---|---|---|
| P1 | `src/voice/`: VAD (lifted), STT op (lifted), TTS sentence op (lifted), sentence cutter; deps onnxruntime, soxr, scipy; `models/silero_vad.onnx`; `audio_worker:` in resources.yaml | Unit tests: the cutter; a recorded TTS sentence fed through VAD → one utterance → STT gives the words back (real services, a few calls) |
| P2 | `assistant_voice_flow` + the `assistant_voice` websocket service (declared before the UI mount), sign-in and Origin check | A scripted client streams a spoken question in real time and receives heard → asked; sends a `say` and receives voice frames |
| P3 | Panel: mic button, capture (AudioWorklet), caption, play queue, Dừng, mic paused while busy/speaking; permissions-policy | Desktop and phone screenshots; a real spoken question answered aloud on :8040 / a worktree server |
| P4 | Measure: end of speech → asked, asked → first sound, per-sentence synthesis | Numbers in this plan (§4) |

## 4. Measured (2026-10-27)

The question "Tổng tài sản của tôi hiện nay là bao nhiêu?" spoken by the TTS voice (2.4 s), fed back as the microphone.

| Step | Where | Time |
|---|---|---|
| end of speech → heard (VAD's 500 ms end + STT) | the real services, a scripted client (2 runs) | +0.65 s |
| end of speech → asked (+ the rest of `VOICE_SILENCE_MS` 1200) | same | +1.18 s |
| asked → first sentence playing (the model's first sentence, its tools first, + TTS) | Chromium, fake microphone, C01, Haiku | 5.8 s desktop, 3.8 s phone |
| one sentence's synthesis | ZipVoice | 117–211 ms |

The transcript came back as said ("tổng tài sản của tôi hiện nay là bao nhiêu"); "7,54" and "09/10/2026" were read whole.
In the browser, desktop and phone, light and dark: Mời bạn nói… → the caption → Đang tìm câu trả lời… → Đang đọc câu
trả lời with each sentence as it plays → the microphone listens again; the spoken bubble wears the microphone; a typed
question after it is the typed flow (no voice rule, no icon); no horizontal scroll, no console errors. The wait after
asking is the turn's own (the same for a typed question): the first sentence plays as soon as the model has written it.

Tests: `tests/test_voice.py` — the cutter, markdown read as prose, Dừng, the door end to end through the real VAD
(fake STT/TTS), another site's page and a signed-out visitor refused, the real services round trip (skipped without keys).

## Appendix — the owner's brief (2026-10-26)

> Implement voice interaction for the assistant, referencing the existing VAD service in the staging branch of
> `educa-reminder-agent` and the current real-time callbot implementation. Reuse existing VAD, STT, and TTS services;
> do not rebuild these components. Stream user audio into STT and process recognized text incrementally… Use a
> configurable silence threshold (e.g. 1 second) to detect when the user has finished speaking and trigger the
> response. Stream the assistant's response through TTS in sentence-sized chunks, splitting at punctuation or
> end-of-line boundaries… play each chunk as soon as it is ready. Adapt the interaction for elderly users: prioritize
> a supportive, patient conversational pace… allowing users time to read their information and fortunes and ask
> follow-up questions. Keep the implementation minimal and consistent with the current architecture; do not invent
> new services or duplicate existing capabilities.

> (correction) VAD is already a type of streaming, and splitting the answer by sentence with TTS is already a type of
> streaming too.
