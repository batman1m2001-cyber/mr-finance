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
