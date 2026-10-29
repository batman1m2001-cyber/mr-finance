# FEAT-44 — Asset allocation: three buckets

| | |
|---|---|
| Type | Extension (owner BRD, 2026-10-28) |
| Requirements | OWN-AA-01…17 ([owner_requirements](../requirements/owner_requirements.md#aa--asset-allocation-in-wealth-planning-advisor-2026-10-28)); the BRD verbatim: [`docs/ASSET_ALLOCATION_BRD.md`](../../ASSET_ALLOCATION_BRD.md) |
| Users | the client (read), the RM (read, send to the review queue), the CIO (tilts the model) |
| Entry points | [SCR-CL-13](../ux/screens/client.md#scr-cl-13--phân-bổ-tài-sản-asset-allocation): client `#/client/muc-tieu/phan-bo`, RM `#/rm/khach-hang/phan-bo`; the tilt panel on the CIO's view page `#/cio/nhan-dinh/<view>`; `POST /api/allocation` (+ `/example`, `/tilt`, `/tilts`, `/send`) |
| Plan | the BRD's §15: P0, P1 and P2 built (P2 2026-10-28) |
| Status | built (2026-10-28) |

## Purpose

Turn a family's holdings, cash flow and risk level into three buckets — **Thanh khoản** (money that must be ready),
**Di sản** (what they want to leave), **Tăng trưởng** (return the rest must earn) — each with a target, a gap and the
actions that close it, worked out by formula so the RM can show every number.

## Behaviour

1. **Buckets.** Cash and deposits are Thanh khoản; real estate, business and insurance are Di sản; the rest is
   Tăng trưởng. The buckets plus the loans equal Tổng quan's net worth.
2. **Liquidity.** A cash-flow table over H years (3 by default): certain income (wages, pensions, rent), spending,
   loan payments, dated events; its lowest month; a +1 point rate line for floating loans. The target three ways
   (A, B, C, [Q-28](../requirements/open_questions.md#q-28--which-liquidity-target-is-the-default)); A decides the
   actions until the owner chooses. The money is laddered in deposits and government bonds by when it is needed.
3. **Fill, then rebalance.** The gap is filled first, comparing wait, sell (the most overweight class) and borrow
   (only under §8.2's conditions). Growth is then rebalanced to the model of the client's level, tilted by the CIO.
4. **Model and tilts.** One model per risk level (cash, bonds, equity, gold, with ranges). The CIO tilts a class
   overweight or underweight from an approved view: 2 points a tilt, at most ±5, inside the range, always 100 %.
   An action moved by a tilt names its view.
5. **Legacy and the goal.** The Legacy floor (debts, the family's spending until the youngest is 22, school fees)
   and target; a gap is talked over (insurance with a beneficiary), a Legacy asset is never sold. The return the
   retirement goal needs against the model's expected one; when short, the choices (save more, retire later) —
   the level is never raised.
6. **Checks.** Each action PASS, WARN or BLOCK. BLOCK: above the level's range, into an excluded class, one position
   over the concentration limit, Liquidity left short, forbidden words. WARN: a class already over the limit, a risk
   test older than 12 months, a simulated level. A BLOCK never reaches the client; the RM sees why.
7. **Words.** Class level only — no ticker, no target price, no FR-604 phrase; the same input gives the same answer
   (no model call).
8. **Send.** The RM's **Gửi vào hàng duyệt** puts the actions (never a blocked one) in the review queue (FEAT-27).
   Who approves in the bank's version is [Q-29](../requirements/open_questions.md#q-29--who-approves-an-allocation-action).

## Worked example

K-7F3A (`data/allocation_example.json`, `/api/allocation/example`) gives the BRD's §11 numbers: Liquidity 19 / gap 11;
Legacy 40.5 / 60 / gap 16–24; Growth 31 rebalanced −3.7 / +2.9 / −2.9 / +3.7; expected 8.3 % against 9.2 % needed.

## P2 (built 2026-10-28)

- **The CIO approves each action** on CIO › Phân bổ (`#/cio/phan-bo`, SCR-CIO-17); the client sees only the approved
  ones ([Q-29](../requirements/open_questions.md#q-29--who-approves-an-allocation-action) resolved).
- **An RM moves a holding** to another bucket with a reason; the CIO's page and Compliance's log list every move.
- **Black–Litterman** beside the ±2-point tilts, inside the same guards; the CIO picks the method every client uses.
- **11 asset classes:** “Theo 11 loại tài sản” on SCR-CL-13 reads the household and the Growth model by the classes
  the news labels use.

## Tests

`tests/test_allocation.py` (every OWN-AA row cites its test in the traceability matrix); the page in
`tests/ui/test_routes.py` and `tests/ui/test_how.py` (every figure has its formula).
