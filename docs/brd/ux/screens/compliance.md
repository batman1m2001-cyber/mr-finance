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
name with its ticker and aliases — Sao Mai Land, Hòa Bình Energy, Kim Phát Holdings). Releasing is audited and unblocks approval condition *g* of the events that held it. Only Compliance may release
(server check; DEF-03 fixed 2026-10-15).
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
| Data | `GET /api/audit`, `GET /api/audit/verify`, `GET /api/audit/export` |
| Screenshot | [desktop](../../assets/current_ui/SCR-CMP-03_desktop-light.jpg) |

The verification result on top (intact, with the algorithms in use, and the note that the database blocks edits
and deletes — or “Gãy ở dòng n” with the reason), then the latest 200 rows: #, Lúc, Ai, Việc, Đối tượng, the first
12 characters of the hash. **Tải JSON (kèm kiểm tra chuỗi)** and **Tải CSV** download the whole chain (2026-10-16).

---

## SCR-CMP-04 — Bản tin (newsletter approval)

| | |
|---|---|
| Route | `#/compliance/ban-tin`, one letter `#/compliance/ban-tin/NL-0001` |
| Feature | [FEAT-17](../../features/FEAT-17-cio-newsletter.md) |
| Requirements | BRD-FR-801, BRD-RULE-SEC-04 |
| Data | `GET /api/newsletters`, `GET /api/newsletters/{id}`, `POST /api/newsletters/act` |
| Screenshots | [an approved letter, desktop](../../assets/current_ui/SCR-CMP-04_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-CMP-04_phone-light.jpg) |

The CIO's list without the form, and the same letter page; while a letter waits, **Tuân thủ duyệt** has a note
(“trả lại: từ 10 ký tự”) with **Duyệt** and **Trả lại**. An earlier send to Private shows as a warning badge with
both times and the CIO's reason. Refusals come back as messages: the author cannot approve, the check fails, the
note is too short.

---

## SCR-CMP-05 — Chính sách (policy radar)

| | |
|---|---|
| Route | Compliance `#/compliance/chinh-sach`, one document `#/compliance/chinh-sach/PD-0001`; CIO `#/cio/chinh-sach[/PD-…]` (read only) |
| Feature | [FEAT-16](../../features/FEAT-16-policy-agent.md) |
| Requirements | BRD-FR-306, BRD-RULE-AI-01, BRD-RULE-SEC-04 |
| Data | `GET /api/policy?since=`, `GET /api/policy/{id}`, `POST /api/policy`, `/api/policy/verify`, `/api/policy/status`, `/api/policy/summarise` |
| Screenshots | [radar, desktop](../../assets/current_ui/SCR-CMP-05_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-CMP-05_phone-light.jpg) · [a document, desktop](../../assets/current_ui/SCR-CMP-05-document_desktop-light.jpg) · [phone](../../assets/current_ui/SCR-CMP-05-document_phone-light.jpg) |

**Radar.** “Radar chính sách” with the **Đề xuất** badge and one paragraph saying it is our reading (Q-09);
“<n> văn bản theo dõi · <m> thay đổi từ lần xem trước”; counts by status; for Compliance a folded **Thêm văn bản**
form (a gazette address, or an official address with title, number, issuer, date, status and pasted text); the
documents by last change, each with **Mới** / **Thay đổi** since the reader's last look, number · issuer · date,
whether the source is verified and the document summarised, its status path and its status badge.

**One document.** **Tóm tắt của Agent Chính sách** (AI and model, or “Mô phỏng — không gọi mô hình”; the run id,
time and attempts; the summary; each point with its article and its quote — a click scrolls to the quote, marked in
the text below; “Nội bộ — không gửi khách hàng”), **Chạy Agent Chính sách** for Compliance once verified; **Văn
bản**, the text with article headings and the quotes marked, and where it came from (the signed PDF and its hash);
beside it **Nguồn** (address, who added it, and the verification or, for a second Compliance person, the form to
verify), **Cập nhật trạng thái** (Compliance) and **Lịch sử**.

## SCR-CMP-06 — Bàn kiểm soát (Compliance desk)

| | |
|---|---|
| Route | `#/compliance`, `#/compliance/ban`; every other Compliance address opens its page as a sheet over the desk |
| Feature | [FEAT-41](../../features/FEAT-41-role-desks.md) (and the pages it gathers: FEAT-02, 03, 11, 14, 15, 16, 17, 18) |
| Requirements | OWN-MR-01, OWN-MR-06, OWN-MR-07, OWN-MR-10; BRD-BR-03, BR-04, FR-306, FR-701, FR-702, FR-801 |
| Data | `GET /api/desk` — the held news, research, letters, policy documents and configuration the pages read, the audit check, the bell's alerts for Compliance |
| Screenshots | [desktop](../../assets/current_ui/SCR-CMP-06_desktop-light.jpg) · [a lane picked, dark](../../assets/current_ui/SCR-CMP-06-pick_desktop-dark.jpg) · [phone, dark](../../assets/current_ui/SCR-CMP-06_phone-dark.jpg) |

**Centre.** Header “Tuân thủ · Bàn kiểm soát” with “<n> việc chờ Tuân thủ · <a> cảnh báo đang mở” and a pill for the
chain. Six lanes, each a button with its icon, name and rule, then its steps as numbers joined by arrows (“1 Chờ phát
hành → 0 Đã phát hành → 0 Từ chối”), the first in amber when something waits and the lane's border amber; the chain's
lane (“657 dòng → ✓ băm khớp → 0 đoạn chỉ-ghi-một-lần”) opens Nhật ký. Below: **Chờ Tuân thủ** (oldest first: title,
control, detail, age, “Chờ bạn” or “Chưa tới giờ”) and **Cảnh báo**. A phone puts each lane's name above its steps.

**Thông tin (a lane picked).** The rule and the step counts, each item waiting (opening its own page), “Mở <page>”.

