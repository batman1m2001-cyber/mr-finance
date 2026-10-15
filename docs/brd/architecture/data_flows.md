# Data flows

## 1. One event, from news to the family (BRD Figure 1)

Redrawn by us from BRD §5 (Figure 1, “AI soạn kịch bản, máy tính con số, người duyệt trước khi tới gia đình”).
Colours of the BRD's legend: blue = AI, orange = a human checkpoint, grey = client data.

```mermaid
flowchart TB
  intl["Tin quốc tế<br/>Fed, international business press"] --> col
  dom["Tin trong nước<br/>press, policy documents"] --> col
  res["Nghiên cứu độc quyền TCB<br/>only when Compliance releases"]:::human --> col
  col["Thu thập tin · every 10 min<br/>white list · restricted list · grouping into events"]
  subgraph zone["AI zone — reads no client data"]
    cio["Agent CIO<br/>macro & rates · equities & funds · credit & RE · commodities & other<br/>→ debate → 2–4 scenarios → format check"]:::ai
    ch["Agent Phản biện<br/>another model · owned by Compliance"]:::ai
  end
  col --> cio --> ch --> appr
  appr["CIO duyệt kịch bản thị trường<br/>edit probabilities, shock sizes · give reasons"]:::human
  appr -- "trả lại để sửa" --> cio
  appr -- "đã duyệt" --> eng["Động cơ kịch bản<br/>VND gain/loss, bad · base · good<br/>per asset, asset class, loan"]
  fam["Dữ liệu gia đình<br/>portfolio, loans, goals"]:::data --> eng
  eng --> pc["Hậu kiểm<br/>concentration, stale prices"]
  pc -- "bad case < 5 %" --> upd["Cập nhật tới gia đình<br/>bad · base · good, 3 horizons"]
  pc -- "bad case ≥ 5 % / 3 months" --> rm["RM xem trước<br/>before anything reaches the client"]:::human
  classDef ai fill:#e6f0fc,stroke:#2a78d6
  classDef human fill:#fcebe1,stroke:#c4561f
  classDef data fill:#eeeeee,stroke:#6b6785
```

Here: FEAT-01 → 02 → 04 → 05 → 06 → 07/08 → 13. The “update to the family” is an in-app page, nothing is sent.

## 2. What data each part reads (the barrier, as implemented)

| Part | Reads | Never reads |
|---|---|---|
| News ingestion (FEAT-01) | public feeds, news config | anything about clients |
| CIO agent, challenger (FEAT-04, 05) | the event's news, released research, catalogues, the 15 factors and shock library | families, holdings, goals, results, audit, restricted-list config |
| Preview (FEAT-06) | branches, factor model | families |
| Application run (FEAT-08) | approved branches, factor model, every family's consolidated holdings, market | — (no AI) |
| Goal branch (FEAT-10) | released regulation notes, goals (dated outflows, declarations) | AML data (none exists), holdings |
| Trace (FEAT-09) | a run, its snapshot, view, event, news | — (staff only) |
| Statement reading, declarations (FEAT-22, 23) | the client's file or message → the model **when AI is on** | — (pre-BRD; bank deployment must keep this in-bank) |

## 3. The two zones (BRD Figure 3)

Redrawn by us from BRD §7.1 (Figure 3). **This is the BRD's target, not what runs here**
([ADR-0009](../decisions/ADR-0009-ai-barrier-by-graph-inputs-in-one-process.md)).

```mermaid
flowchart LR
  subgraph ext["External AI zone — own infrastructure and database"]
    pub[Public news] --> ag["CIO agent, challenger, policy agent<br/>scenarios, probabilities, core shocks"]
    rc["TCB research<br/>released copies"] --> ag
    ag --> adb[("AI-zone DB<br/>news, factor model, runs, results")]
    adb --> out[Outbox]
  end
  subgraph tcb["TCB system — client data never leaves"]
    rel[Compliance releases research] -- "released copy" --> rc
    inbox["Inbox · format check"] --> cioapp[CIO approves scenarios]
    cioapp --> eng["Scenario engine<br/>+ family and goal data"]
    eng --> rmc[RM pre-review, client]
  end
  out -- "signed results only" --> inbox
```

## 4. Money and evidence through an application run

```mermaid
flowchart LR
  view["approved view<br/>branches"] --> snap
  hold["consolidated holdings<br/>every family"] --> snap
  mkt["market (hash, date)"] --> snap
  fm["factor model (whole)"] --> snap
  snap["run_snapshots<br/>SHA-256"] --> comp["compute (pure)"] --> res["family_impacts<br/>bands · contributions · flags"]
  res --> pc["post-check P1–P5"] --> st{"critical?"}
  st -- no --> eff[EFFECTIVE] --> reads["RM today · family impact · exposure"]
  st -- yes --> hold2[NEEDS_CIO_REVIEW]
  snap -. "verify: recompute = stored, to the dong" .-> res
```

Every arrow that writes also appends to `audit_log` in the same transaction.
