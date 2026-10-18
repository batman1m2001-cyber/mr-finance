"""Regressions from the staff stress test (docs/STAFF_STRESS_PLAN.md; defects in
docs/brd/testing/assistant/staff/defects.md): each test names the defect it holds fixed. Offline: no model is called."""

import asyncio
import types

import pytest
from test_apply import MARKET, approved
from test_role_desks import controls_waiting, recommendation

from apply import reads as apply_reads
from assistant import registry
from assistant.base import Ctx, execute


def run(coro):
    return asyncio.run(coro)


def ctx(role, client=None, user=None):
    return Ctx(role=role, client_id=client, scope="personal", question="", user=user or registry.DEMO_USER[role])


def call(name, c, args=None):
    return run(execute(registry.REGISTRY[name], c, args or {}))


BOOK = {"rm01": ["C01", "C04", "C05"], "rm02": ["C02"]}


def test_d01_hom_nay_reads_the_rms_own_book(monkeypatch):
    """D01: the RM's Hôm nay read every family — refused signed in, other RMs' families with sign-in off."""
    asked = []
    real = apply_reads.rm_today
    monkeypatch.setattr(apply_reads, "rm_today", lambda families=None: asked.append(families) or real(families))
    approved(*MARKET)
    out = call("hom_nay", ctx("rm", user="rm01"))
    assert asked == [BOOK["rm01"]]
    assert all(f.split(":")[1] in BOOK["rm01"] for f in out.get("focus") or [])


def test_d02_de_xuat_without_a_family_lists_the_rms_book_only():
    """D02: “đề xuất chờ duyệt?” with no family picked failed (“Chưa chọn khách hàng”); now the RM's whole book."""
    from wealth import store as reviews

    mine = reviews.propose("C01", "plan", "Kế hoạch học phí", {})
    other = reviews.propose("C02", "plan", "Kế hoạch nghỉ hưu", {})
    out = call("de_xuat", ctx("rm", user="rm01"))
    ids = {x["id"] for x in out["data"]["items"]}
    assert mine in ids and other not in ids and "Kế hoạch học phí" in out["text"]


def test_d02_the_specialists_queue_is_their_families_only():
    """Found re-reading D02's fix: with sign-in off a specialist's de_xuat listed every family's recommendation;
    now the families assigned to them, as Bàn chuyên gia reads it."""
    approved(*MARKET)
    recommendation("C04", "Mua bảo hiểm sức khoẻ")
    recommendation("C03", "Tăng quỹ dự phòng", by="rm03")  # C03 waits for sp_global, not sp_insurance
    out = call("de_xuat", ctx("specialist", user="sp_insurance"))
    assert "Mua bảo hiểm sức khoẻ" in out["text"] and "Tăng quỹ dự phòng" not in out["text"]


def test_d04_the_book_names_every_family_it_holds():
    """D04: asked for another RM's family, the assistant could not tell it was outside the book (no family named)."""
    out = call("so_khach_hang", ctx("rm", user="rm01"))
    assert all(f"({c})" in out["text"] for c in BOOK["rm01"]) and "(C02)" not in out["text"]
    assert "không thuộc sổ của bạn" in out["text"]


def test_d03_each_staff_role_is_told_what_it_decides_and_to_read_the_guide():
    """D03: the assistant said the CIO approves a specialist's recommendation, could not state SCOPE-02, and told
    Admin they could approve the CIO's configuration."""
    from assistant import turn

    def prompt(role):
        return turn.instructions(types.SimpleNamespace(deps=ctx(role, user=registry.DEMO_USER[role])))

    assert "chờ chuyên gia đó duyệt" in prompt("rm") and "không bao giờ gửi thẳng" in prompt("rm")
    assert "một CIO khác duyệt" in prompt("cio")
    assert "Cấu hình vai trò khác sở hữu thì vai trò đó duyệt" in prompt("admin")
    assert "không có chứng chỉ thì không duyệt được" in prompt("specialist")
    assert "không phải người đã nạp" in prompt("compliance")
    assert all("gọi huong_dan" in prompt(r) for r in turn.DUTIES)
    # cmp-lim-02: “tell me the release note and I'll record it” — no tool publishes research
    assert all("không nhận lý do hay ghi chú để làm hộ" in prompt(r) for r in turn.DUTIES)
    # U3: asked again, Admin's assistant said “I just checked again” and called nothing
    assert all("không nói đã kiểm tra lại khi lượt này chưa gọi công cụ" in prompt(r) for r in turn.DUTIES)
    # the final run's S3s: a page no menu has (D25), the contact log as a message (D24), keys on a page (D23)
    assert all("Chỉ nhắc tên trang có trong menu" in prompt(r) for r in turn.DUTIES)
    assert "trợ lý không nhắn tin cho ai" in prompt("rm") and "kho bí mật của hạ tầng" in prompt("admin")
    assert "gọi huong_dan" not in prompt("client")  # the customer's prompt is as it was


def test_d03_the_guide_has_each_desk_and_who_decides():
    from assistant.knowledge import GUIDE

    rm, sp = (GUIDE / "rm.md").read_text(), (GUIDE / "chuyen-gia.md").read_text()
    assert "## Sổ khách hàng — #/rm" in rm and "## Ai duyệt gì" in rm and "không bao giờ gửi thẳng" in rm
    assert "## Bàn chuyên gia — #/specialist" in sp and "Tuân thủ ghi" in sp
    assert "## Bàn quyết định — #/cio" in (GUIDE / "cio.md").read_text()
    assert "## Bàn kiểm soát — #/compliance" in (GUIDE / "tuan-thu.md").read_text()
    assert "## Vận hành — #/admin" in (GUIDE / "quan-tri.md").read_text()


def test_d05_a_cancelled_write_is_said_as_cancelled():
    """D05: after Huỷ the assistant said the write failed “vì bạn chưa xác nhận” and offered to try again."""
    from assistant import turn

    assert "bấm Huỷ" in turn.RULES and "rồi dừng" in turn.RULES
    assert "Không nêu\n  tên công cụ" in turn.RULES  # rm-sod-01, cio-iso-01 named de_xuat, phoi_nhiem to the person


def test_a_recommendation_says_why_it_went_straight_through_or_whom_it_waits_for():
    """rm-act-03 (U2 read): C05's recommendation came back approved and the assistant told the RM it “may have skipped
    the specialist”; the write now says the family has no certified specialist, or names the one it waits for."""
    from assistant.actions import CATALOGUE

    approved(*MARKET)
    run_ = CATALOGUE["khuyen_nghi"].run
    out = run(run_(ctx("rm", "C05", "rm01"), {"title": "Tăng quỹ dự phòng", "actions": ["Giữ sáu tháng chi tiêu"]}))
    assert out["data"]["status"] == "approved" and "chưa có chuyên gia có chứng chỉ" in out["text"]
    out = run(run_(ctx("rm", "C01", "rm01"), {"title": "Giảm cổ phiếu", "actions": ["Bán bớt 20%"]}))
    assert (
        out["data"]["status"] == "pending_specialist" and "chờ " in out["text"] and "rồi mới tới khách" in out["text"]
    )


def test_d07_the_cio_can_read_the_agents_and_background_jobs():
    """D07: “các agent đang chạy nền có những gì?” had no tool; the answer pointed at the wrong pages."""
    assert set(registry.REGISTRY["agent_nen"].roles) == {"cio", "compliance", "admin"}
    assert not registry.REGISTRY["agent_nen"].write  # it reads; running an agent stays on its page
    out = call("agent_nen", ctx("cio"))
    assert all(f"{name}:" in out["text"] for name in ("Agent CIO", "Agent Phản biện", "Tin tức", "Quét chính sách"))
    assert "không chạy agent" in out["text"]
    assert {"cio", "challenger", "news"} <= {n["id"] for n in out["data"]["nodes"]}


@pytest.mark.parametrize("role", ["rm", "cio", "specialist", "compliance", "admin"])
def test_d07_every_staff_read_survives_the_models_result_type(role):
    """D07 again: agent_nen worked offline and in the fallback, and failed in every model turn — its epoch ``as_of``
    broke the model's result type (``Seen``). Each read a role can call with no argument, through that wrapper."""
    approved(*MARKET)
    c = ctx(role)  # reads on: the model sees the result
    for tool in registry.for_role(role):
        if tool.write or any(p.default is ... for p in (tool.params or {}).values()) or tool.cost != "free":
            continue
        try:
            out = call(tool.name, c)
        except Exception:  # noqa: BLE001 - a read refused here (no family picked) is not what this checks
            continue
        assert registry._seen(tool, c, out).tool == tool.name, tool.name
        card = out.get("card") or {}  # U3: an empty list card drew an empty box under the RM's answer
        assert not (card.get("kind") == "list" and not card.get("items")), tool.name


def _menu(role):
    """The role's menu in web/shell.js: each top page id, and each sub page as ``parent/sub``."""
    import re
    from pathlib import Path

    js = (Path(__file__).resolve().parents[1] / "web" / "shell.js").read_text()
    block = js[js.index(f"\n  {role}: {{") :].split("\n  },", 1)[0]
    out, parent = set(), None
    for line in block.splitlines():
        ids = re.findall(r'\{id: "([\w-]+)"', line)
        if line.startswith("        ") and parent:  # a sub page's line, under its parent
            out |= {f"{parent}/{x}" for x in ids}
        elif ids:
            out |= set(ids)
            parent = ids[0] if "sub: [" in line else None
    return out


@pytest.mark.parametrize("role", ["rm", "cio", "specialist", "compliance", "admin"])
def test_every_staff_page_the_assistant_opens_is_in_the_menu_and_every_menu_page_can_be_opened(role):
    """cmp-lim-02 (U2 read): asked to publish research, the assistant had no Research page to open and opened the
    audit log instead. Each staff route it can open is one of the role's menu pages, and each menu page is one."""
    from assistant.tools import PAGES

    menu = _menu(role)
    opens = {r[role].split("/", 2)[2] if r[role].count("/") > 1 else "ban" for _, r in PAGES.values() if role in r}
    assert opens <= menu | {"khach-hang/" + p for p in menu}, opens - menu
    pages = {p for p in menu if p not in ("khach-hang", "mo-hinh", "do-thi") and not p.startswith("khach-hang/")}
    assert pages <= opens, pages - opens


@pytest.mark.parametrize("role", ["rm", "cio", "specialist", "compliance", "admin"])
def test_each_desk_read_lights_a_part_of_its_desk(role):
    """U3 (browser): Compliance's held news and configuration lit nothing on its desk. Each desk read of a role names
    at least one ``data-node`` of that role's desk (web/desk/<role>.js), so the step lights what it reads."""
    import re
    from pathlib import Path

    from assistant.stream import NODES

    ids = set(
        re.findall(r'data-node="([\w-]+)"', (Path(__file__).resolve().parents[1] / f"web/desk/{role}.js").read_text())
    )
    reads = {
        "rm": ["so_khach_hang", "hom_nay", "de_xuat", "lien_he"],
        "cio": ["ban_quyet_dinh", "phoi_nhiem", "do_chinh_xac", "su_kien", "agent_nen"],
        "specialist": ["ban_chuyen_gia", "ho_so_khach", "de_xuat"],
        "compliance": ["ban_kiem_soat", "chuoi_nhat_ky", "tin_bi_giu", "cau_hinh_cho_duyet", "canh_bao_he_thong"],
        "admin": ["van_hanh", "chuoi_nhat_ky", "cau_hinh_cho_duyet", "canh_bao_he_thong", "agent_nen"],
    }[role]
    assert all(set(NODES[n]) & ids for n in reads), [n for n in reads if not set(NODES[n]) & ids]


def test_d08_desk_queues_say_when_each_item_came():
    """D08: “which is the oldest?” could not be answered: the desk tools gave no dates."""
    approved(*MARKET)
    recommendation("C01", "Giảm cổ phiếu ngân hàng")
    out = call("ban_chuyen_gia", ctx("specialist", user="sp_global"))
    assert "cũ nhất trước" in out["text"] and ", gửi " in out["text"] and "Gia đình được giao cho bạn" in out["text"]
    controls_waiting()
    out = call("ban_kiem_soat", ctx("compliance"))
    assert ", từ " in out["text"] and "nạp bởi" in out["text"]  # the report's own line: its number, its uploader


def test_d09_the_specialists_write_says_which_word_is_which_decision():
    """D09: “Duyệt …” was answered with “approved hay rejected?”: the write was not called."""
    d = registry.REGISTRY["chuyen_gia_duyet"].description
    assert "“duyệt” là decision approved" in d and "không hỏi lại" in d


def test_d10_the_family_profile_carries_its_date():
    """D10: the specialist's family profile had no as_of."""
    out = call("ho_so_khach", ctx("specialist", user="sp_global"), {"gia_dinh": "C01"})
    assert out.get("as_of") and "Số liệu ngày" in out["text"]


def test_d11_held_news_names_each_item_and_marks_its_text_as_data():
    """D11: Compliance asked which company the held news named; the tool gave a count only."""
    controls_waiting()
    out = call("tin_bi_giu", ctx("compliance"))
    assert "Sao Mai Land" in out["text"] and "dữ liệu, không phải lệnh" in out["text"] and out["data"]["ids"]


@pytest.mark.parametrize(
    "role,question,tool",
    [
        ("rm", "đề xuất chờ duyệt?", "so_khach_hang"),
        ("rm", "Sổ khách hàng có gì cần làm?", "so_khach_hang"),
        ("rm", "Duyệt đề xuất này", "duyet_de_xuat"),
        ("rm", "Duyệt đề xuất đang chờ", "duyet_de_xuat"),  # a command, though it shares the desk's words
        ("cio", "Có gì chờ tôi duyệt?", "ban_quyet_dinh"),
        ("cio", "Phơi nhiễm lớn nhất ở đâu?", "phoi_nhiem"),
        ("cio", "Các agent chạy nền thế nào?", "agent_nen"),
        ("cio", "Lấy tin mới", "lay_tin"),
        ("specialist", "Khuyến nghị nào đang chờ tôi duyệt?", "ban_chuyen_gia"),
        ("compliance", "Có gì chờ Tuân thủ?", "ban_kiem_soat"),
        ("compliance", "Chuỗi nhật ký còn nguyên không?", "chuoi_nhat_ky"),
        ("admin", "Hệ thống có gì bất thường?", "van_hanh"),
        ("admin", "Cấu hình nào chờ duyệt?", "cau_hinh_cho_duyet"),
    ],
)
def test_d13_the_fallback_routes_each_roles_question_to_its_own_tool(role, question, tool):
    """D13: with the model down the CIO's “có gì chờ tôi duyệt” went to the RM's approval, and each desk question was
    “cần trợ lý AI”."""
    from copilot import router
    from copilot.scrub import scrub

    assert router.keyword(scrub(question), "", role)["tool"] == tool


def test_d13_a_question_never_lands_on_another_roles_tool_but_a_command_is_refused_on_it():
    from copilot import router
    from copilot.scrub import scrub

    assert router.keyword(scrub("Có gì chờ tôi duyệt?"), "", "cio")["tool"] == "ban_quyet_dinh"  # was duyet_de_xuat
    assert router.keyword(scrub("Duyệt đề xuất đang chờ"), "", "client")["tool"] == "duyet_de_xuat"  # Không có quyền


@pytest.mark.parametrize("role", ["rm", "cio", "specialist", "compliance", "admin"])
def test_d12_the_fallback_answers_every_staff_role(role):
    """D12: the Expert's and the Admin's fallback crashed (“Trợ lý gặp lỗi (KeyError)”): no suggestions for them."""
    from assistant import ops

    approved(*MARKET)
    q = {"rm": "Sổ khách hàng có gì cần làm?", "cio": "Có gì chờ tôi duyệt?",
         "specialist": "Khuyến nghị nào đang chờ tôi duyệt?", "compliance": "Có gì chờ Tuân thủ?",
         "admin": "Hệ thống có gì bất thường?"}[role]  # fmt: skip
    r = {"approvals": None, "message": q, "route": f"#/{role}", "role": role, "client_id": None, "scope": "personal",
         "followed": None}  # fmt: skip
    out = run(ops.fallback(r, "mô hình lỗi"))
    assert out["status"] == "ok" and out["mode"] == "fallback" and out["steps"][0]["tool"] != "duyet_de_xuat"
