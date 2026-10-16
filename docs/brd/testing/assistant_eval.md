# The assistant's eval on a real model

`scripts/eval_assistant.py` runs every case of [`data/assistant_eval.json`](../../../data/assistant_eval.json)
through the served `assistant_flow`, with the client-data barrier installed, on a copy of the live state file. For
each turn it checks:

- the tools called, and the status: an answer, or a write waiting for the person;
- for a request no tool supports: that the turn says it cannot, and calls no write;
- that another client's figures never appear;
- grounding: every number in the answer is one the tools returned or the question gave (to 1 %, by size).

The model is `llm:copilot` (`LLM_MODEL_COPILOT`).

```
.venv/bin/python scripts/eval_assistant.py --env ../mr-finance/.env --state ../mr-finance/data/state.db --subset A2
```

## A2 subset (2026-10-17): 10 cases — 6 multi-step, 2 writes, 2 refusals

| Run | Model | Passed | Latency p50 / p95 | Tokens per turn |
|---|---|---|---|---|
| 1 (before fixes) | anthropic/claude-haiku-5.5 | 6 / 10 | 5.6 / 6.9 s | 5,369 |
| 2 | anthropic/claude-haiku-5.5 | 10 / 10 | 5.3 / 9.8 s | 6,153 |
| 3 | anthropic/claude-haiku-5.5 | 10 / 10 | 5.5 / 7.0 s | 5,813 |

### What run 1 found

- **One real failure (write-02).** Asked to send a scenario option to the RM, the model ran the scenario, then asked
  in prose "Bạn có muốn tôi gửi…?" instead of calling the write. In the panel, the confirm button would never have
  appeared. Fixed in the instructions: call the write tool directly; the system asks for the confirmation.
- **Three grader faults.**
  - multi-02: “giảm 1,82 tỷ” states the tool's “−1,82 tỷ”; numbers are now compared by size.
  - refuse-01: “500 triệu” came from the question itself.
  - refuse-02: the injected name came from the question. The model searched, found nothing visible to the client,
    and refused. The check is now that the other client's own figures never appear.

### Cost

Cost per turn is not yet reported: `llm:copilot` declares no token prices, so operonx-agents' `Usage.cost_usd` is
empty and the cost cap is not set (ADR-0034). A8 measures it.

## A5 (2026-10-17): the guide, and the web

**The guide** (free, in the test suite): `data/assistant_guide_questions.json`, 24 product questions over every
role, paraphrased and some without accents, each with the page that answers it; and
`data/assistant_reference_questions.json`, 10 questions on a formula or a term.

| Search | First three | First | MRR | Median search | Paid calls |
|---|---|---|---|---|---|
| Lexical (FTS5, Vietnamese bigrams, accents folded) — **chosen** | 24 / 24 | 20 / 24 | 0.91 | 35 ms | 0 |
| Hybrid, + `baai/bge-m3` embeddings via OpenRouter | 24 / 24 | 21 / 24 | 0.93 | 1,040 ms | 31 embedding requests |
| Lexical, formulas and glossary in the same ranking | 22 / 24 | 17 / 24 | — | — | 0 |
| Lexical, pages and references searched apart — **built** | 24 / 24 | 20 / 24 | — | — | 0 |

The formula or term asked about came first among the references on 10 / 10. Asserted in
`tests/test_assistant_knowledge.py` (first three 24/24, first ≥ 20; references 10/10).

**The web** (one question, the State Bank's policy rate, after the two fixes in ADR-0030): 9.1 s, US$0.012, 14,911
prompt and 1,225 completion tokens, one search request, two cited sources (one dated October 2026) whose different
figures the answer named; certainty “trung bình”. Building it took five real calls, about US$0.06. The outside-topic
cases of the full suite are A8.

## A6 (2026-10-17): the consolidator and follow-ups

**Consolidator**, five client conversations (2–11 turns) on `anthropic/claude-haiku-5.5`, one tick:

| Conversation | Prompt / answer tokens | Cost (US$) | Items kept |
|---|---|---|---|
| a preference, a goal, a constraint (4 turns) | 906 / 359 | 0.00027 | 3 |
| a job, a reserve (3 turns) | 774 / 279 | 0.00022 | 2 |
| a rates question and “cảm ơn” (2 turns) | 531 / 39 | 0.00007 | 0 |
| ten spending questions and one standing request (11 turns) | 2,372 / 115 | 0.00029 | 1 (the request) |
| retirement, risk, a spouse, travel (3 turns) | 658 / 607 | 0.00037 | 5 (the spouse's name not kept) |
Total US$0.0012, 22 s (4.5 s a conversation, one at a time), none refused, none failed. Characters per prompt token
1.64–1.70: the budget's estimate was corrected from 3 to 1.6 before release.

**Follow-ups**, two requests on the real model: “Báo tôi khi VN-Index xuống dưới 1.200 điểm” → the confirm line
“Báo cho bạn một lần khi VN-Index dưới 1.200 điểm (theo dõi 30 ngày)?”; “Khi nào có tin được duyệt về lãi suất thì
nhắc tôi nhé” → “… khi có sự kiện được duyệt về “lãi suất” …”. 5,164 and 5,168 prompt tokens. Checking costs no
model call.
