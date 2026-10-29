# OneWealth — English and Vietnamese: plan

**Status: done 2026-10-27** (owner's request that day: "the language switch button EN/VI, with English is the default";
scope picked the same day: **screens + assistant**). Results in §5.

## 1. What exists

- Every word on screen is Vietnamese, written straight into the pages: about 2,160 different phrases in 11,000 lines
  of `web/`, plus the labels the server sends (asset kinds, alerts, statuses) from `src/`.
- Numbers are Vietnamese in `web/core/core.js` (`vnd`: “1,25 tỷ”, `ago`: “3 phút trước”).
- The assistant is told in `src/assistant/turn.py` `RULES`: “Trả lời bằng tiếng Việt”.
- Voice uses the callbot's Vietnamese speech services (STT fastconformer, TTS ZipVoice).
- The iPhone app is the site in a shell, so it gets whatever the site does.

## 2. Scope

| Switches to English | Stays as written |
|---|---|
| Every button, menu, heading, label, table header, tip, empty/error state, footer | News headlines and articles |
| The labels and alerts the server sends | AI-written scenario text and agent write-ups |
| Numbers, money and “… ago” | Client, family and asset names |
| The assistant's answers and its fixed sentences | What a person typed |

## 3. Decisions

**L1. One switch, one place.** `EN | VI` next to the theme button; English unless the viewer picked Vietnamese
(`localStorage mf.lang`). Switching reloads the page, so every number and page is drawn once in the new language.

**L2. A phrase book, not 2,600 edits.** `web/core/i18n.js` translates the page as it is drawn: each text and each
`placeholder`, `aria-label`, `title`, `alt` is looked up in `web/core/lang/en.js` (Vietnamese → English). A phrase with
a value in it is a pattern: `"{0} tài sản"` → `"{0} assets"`; the value is translated too when it is itself a phrase.
Not in the book → shown as written (that is how data stays untouched). Inputs and typed text are never touched.
The pages keep their Vietnamese source; the book is the one file a translator edits.

**L3. Numbers in code.** `vnd`, `pct`, `num`, `ago` speak the chosen language: `1.25 bn`, `350 m`, `192 k`, `12.5%`,
`3 min ago`. Money written by the server inside a label (“1,2 tỷ”) is converted when the label is.

**L4. The assistant is told.** The panel sends `lang`; the server's rules say “answer in English” for `en`. Its fixed
sentences go through the same book.

**L5. Voice stays Vietnamese.** The speech services only hear and speak Vietnamese. In English, the mic still works and
a spoken question is answered in Vietnamese (so it can be read aloud); the panel says so in one line.

## 4. Phases and gates

| Phase | What | Gate |
|---|---|---|
| P1 | Switch, `i18n.js`, numbers, the shell (header, nav, footer, sign-in) | Screenshots EN/VI, desktop + phone, light + dark |
| P2 | The book for every page's own text (extracted from `web/`) | Each page opens in EN with no broken layout |
| P3 | A crawl of every role × page in EN lists what is still Vietnamese; the server's labels added | What is left is only data (§2 right column), listed |
| P4 | Assistant in English, its fixed sentences, the voice line | A real EN question answered in English, cost counted |
| P5 | Merge to main, :8030 restarted, the iPhone app checked | Live site opens in English |

## 5. Status

- **P1.** `EN | VI` in the header and in the account menu (phone). Screenshots for client, RM, CIO and admin, EN and
  VI, light and dark, 1440×900 and 390×844: no page wider than the screen.
- **P2.** `web/core/lang/en.js`: 4,224 phrases, generated from the pages' own text plus the server's labels.
- **P3.** A crawl of every role × page in EN. What is still Vietnamese is data, as §2 says: client, family and
  contact names; conversation titles and typed questions; news headlines (also inside “Select …”, “News: …”,
  “Event: …” labels and chart text); asset names (“Holding: Cổ phiếu FPT”); client goals; RM proposal titles and
  “why missed” notes; challenger questions; AI scenario names and write-ups; policy source notes; memory items; old
  assistant answers; the newsletter's factor lists.
- **P4.** The panel sends `lang: "en"`; `turn.py` answers in English unless the question was spoken. Three real
  questions on Haiku 5.5 as C01: “How are my assets doing?” and “What needs my attention?” answered in English
  (US$0.0029–0.0031 each, 2 requests, ~28 k input tokens: the same as in Vietnamese); a spoken question in EN mode
  answered in Vietnamese. The Vietnamese control answer is unchanged. Known limits: the model sometimes writes an
  asset's name without its accents (“Thao Dien”); the template and keyword fallback modes write Vietnamese
  sentences, which the book translates only where they match it.
