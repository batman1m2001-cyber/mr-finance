# Compliance screens (`#/compliance/…`)

Layer C. As built on 2026-10-15 (new pages). Compliance is the demo user `compliance` (Đỗ Minh Châu);
`compliance2` exists for separation of duties.

---

## SCR-CMP-01 — Tin bị giữ (held news)

| | |
|---|---|
| Route | `#/compliance/giu` (Compliance's first page) |
| Feature | [FEAT-02](../../features/FEAT-02-cio-inbox-and-events.md) |
| Requirements | BRD-BR-04, BRD-FR-105, BRD-RULE-ROLE-03 |
| Data | `GET /api/news/inbox?held=1`, `GET /api/news/config`, `POST /api/news/release` |
| Screenshot | [desktop](../../assets/current_ui/SCR-CMP-01_desktop-light.jpg) |

News naming a restricted organisation, each with its outlet, time and the names it mentions (“nhắc tới …”), a
reason field (“Lý do cho phép (bắt buộc)”) and **Cho phép**; beside it **Danh sách hạn chế** (badged “giả lập”: each
name with its ticker and aliases — Sao Mai Land, Hòa Bình Energy, Kim Phát Holdings). Releasing is audited and unblocks approval condition *g* of the events that held it. The server does not check
that the releaser is Compliance (DEF-03).
Empty: “Không có tin nào bị giữ”.

---

## SCR-CMP-02 — Nghiên cứu (research release)

| | |
|---|---|
| Route | `#/compliance/nghien-cuu` |
| Feature | [FEAT-03](../../features/FEAT-03-research-and-regulation-notes.md) |
| Requirements | BRD-BR-03, BRD-FR-202, BRD-FR-203, BRD-RULE-SEC-04 |
| Data | `GET /api/research`, `POST /api/research/release` |
| Screenshots | [desktop](../../assets/current_ui/SCR-CMP-02_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-CMP-02_phone-light.jpg) |

The same list as SCR-CIO-06 without the upload form; each pending item has a note field (“Ghi chú của Tuân thủ (từ
20 ký tự)”) and **Phát hành** / **Từ chối**. Refusals come back as messages: note too short, the uploader cannot
release, release time not reached, restricted-list mention.

---

## SCR-CMP-03 — Nhật ký (audit log)

| | |
|---|---|
| Route | `#/compliance/nhat-ky` |
| Feature | [FEAT-11](../../features/FEAT-11-audit-log.md) |
| Requirements | BRD-BR-12, BRD-FR-702, BRD-NFR-09 |
| Data | `GET /api/audit`, `GET /api/audit/verify` |
| Screenshot | [desktop](../../assets/current_ui/SCR-CMP-03_desktop-light.jpg) |

The verification result on top (intact, with the algorithms in use, and the note that the database blocks edits
and deletes — or “Gãy ở dòng n” with the reason), then the latest 200 rows: #, Lúc, Ai, Việc, Đối tượng, the first
12 characters of the hash. No export (FR-702 gap).
