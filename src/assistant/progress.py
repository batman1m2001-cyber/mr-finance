"""What a step says in the panel while it runs and once it is done (the owner, 2026-10-18: show what the assistant is
doing now, "a message with clear semantic, concise", and nothing unsafe).

Each tool has two fixed sentences. The only details ever added come from the product's own fixed names: a stress
scenario's title, or a month the arguments give as YYYY-MM. The person's free text, an id, any other argument and
every result stay out: a step says what kind of work runs, never what it found."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

# tool → (while it runs, once done); a write waits for the person, so its sentence says what it prepares
SAYS: Dict[str, Tuple[str, str]] = {
    "tong_quan": ("Đang xem tài sản, nợ và phân bổ của bạn", "Đã xem tài sản, nợ và phân bổ"),
    "dong_tien": ("Đang xem tiền vào, tiền ra trong tháng", "Đã xem tiền vào, tiền ra trong tháng"),
    "chu_y": ("Đang tìm những điều cần chú ý lúc này", "Đã xem những điều cần chú ý"),
    "muc_tieu": ("Đang xem tiến độ các mục tiêu", "Đã xem tiến độ các mục tiêu"),
    "tac_dong": ("Đang tính tác động của tin lên tài sản", "Đã tính tác động của tin"),
    "dieu_tra": ("Đang lần theo đường đi của tin tới tài sản", "Đã lần theo đường đi của tin"),
    "kich_ban": ("Đang chạy kịch bản sốc trên tài sản hiện có", "Đã chạy kịch bản sốc"),
    "lien_ket": ("Đang xem mục này nối với những gì", "Đã xem các liên kết của mục"),
    "so_sanh_kich_ban": ("Đang so sánh các kịch bản, riêng và cùng lúc", "Đã so sánh các kịch bản"),
    "gia_dinh": ("Đang chạy giả định của bạn trên tài sản hiện có", "Đã chạy giả định của bạn"),
    "hom_nay": ("Đang xem các gia đình cần xem hôm nay", "Đã xem danh sách hôm nay"),
    "hop_tin": ("Đang đếm tin mới trong hộp tin", "Đã xem hộp tin"),
    "tin_bi_giu": ("Đang xem tin bị giữ", "Đã xem tin bị giữ"),
    "mo_trang": ("Đang tìm trang cần mở", "Đã tìm trang"),
    "tinh": ("Đang tính", "Đã tính"),
    "duyet_de_xuat": ("Đang chuẩn bị duyệt đề xuất để bạn xác nhận", "Đã xử lý đề xuất"),
    "lay_tin": ("Đang chuẩn bị lấy tin mới để bạn xác nhận", "Đã lấy tin mới"),
    "dong_luc": ("Đang xem chính sách và dự án tác động tới tài sản", "Đã xem chính sách và dự án"),
    "tim_kiem": ("Đang tìm trong dữ liệu bạn được xem", "Đã tìm"),
    "de_xuat": ("Đang xem hàng chờ đề xuất", "Đã xem hàng chờ đề xuất"),
    "su_kien": ("Đang xem các sự kiện", "Đã xem các sự kiện"),
    "canh_bao_he_thong": ("Đang xem cảnh báo hệ thống", "Đã xem cảnh báo hệ thống"),
    "lien_he": ("Đang xem các lần liên hệ gần đây", "Đã xem các lần liên hệ"),
    "gui_de_xuat": ("Đang chuẩn bị gửi đề xuất để bạn xác nhận", "Đã xử lý đề xuất"),
    "ghi_lien_he": ("Đang chuẩn bị ghi liên hệ để bạn xác nhận", "Đã xử lý liên hệ"),
    "khuyen_nghi": ("Đang chuẩn bị khuyến nghị để bạn xác nhận", "Đã xử lý khuyến nghị"),
    "chuyen_gia_duyet": ("Đang chuẩn bị duyệt khuyến nghị để bạn xác nhận", "Đã xử lý khuyến nghị"),
    "danh_dau_khan": ("Đang chuẩn bị đánh dấu sự kiện để bạn xác nhận", "Đã xử lý sự kiện"),
    "da_xem_canh_bao": ("Đang chuẩn bị đánh dấu cảnh báo để bạn xác nhận", "Đã xử lý cảnh báo"),
    "nho_lai": ("Đang xem những điều bạn nhờ ghi nhớ", "Đã xem bộ nhớ"),
    "ghi_nho": ("Đang chuẩn bị ghi nhớ để bạn xác nhận", "Đã xử lý việc ghi nhớ"),
    "quen": ("Đang chuẩn bị quên một điều để bạn xác nhận", "Đã xử lý việc quên"),
    "tim_lich_su": ("Đang tìm trong các cuộc trò chuyện trước", "Đã tìm trong lịch sử"),
    "doc_lai_phien": ("Đang đọc lại các lượt trước", "Đã đọc lại các lượt trước"),
    "huong_dan": ("Đang tra hướng dẫn sử dụng", "Đã tra hướng dẫn"),
    "tai_lieu": ("Đang tìm trong tài liệu của bạn", "Đã tìm trong tài liệu"),
    "tim_tren_web": ("Đang tìm trên web", "Đã tìm trên web"),
    "theo_doi": ("Đang chuẩn bị đặt theo dõi để bạn xác nhận", "Đã xử lý việc theo dõi"),
    "theo_doi_cua_toi": ("Đang xem các việc bạn đang theo dõi", "Đã xem việc theo dõi"),
    "huy_theo_doi": ("Đang chuẩn bị huỷ theo dõi để bạn xác nhận", "Đã xử lý việc huỷ theo dõi"),
    # the staff desks (FEAT-41)
    "ban_quyet_dinh": ("Đang xem việc chờ bạn quyết định", "Đã xem việc chờ bạn quyết định"),
    "phoi_nhiem": ("Đang xem phơi nhiễm của mọi gia đình", "Đã xem phơi nhiễm của mọi gia đình"),
    "lan_ap_dung": ("Đang xem các lần áp dụng", "Đã xem các lần áp dụng"),
    "do_chinh_xac": ("Đang xem độ chính xác của mô hình", "Đã xem độ chính xác của mô hình"),
}
MONTH = re.compile(r"(?:(\d{4})-)?(0?[1-9]|1[0-2])")  # “2026-09”, or the month alone (“09”: the latest with data)


def _titles(words: List[Any]) -> List[str]:
    from assistant.graphtools import COMPARE
    from scenarios import _sim

    ids = [COMPARE[w] for w in words if isinstance(w, str) and w in COMPARE]
    return [_sim.SCENARIOS[s]["title"] for s in dict.fromkeys(ids)]


def _detail(tool: str, args: Dict[str, Any]) -> Optional[str]:
    """The one detail a sentence may carry, from the product's own names only."""
    if tool == "dong_tien" and isinstance(args.get("month"), str) and (m := MONTH.fullmatch(args["month"])):
        return f"tháng {int(m.group(2)):02d}" + (f"/{m.group(1)}" if m.group(1) else "")
    if tool == "kich_ban":
        t = _titles([args.get("scenario")])
        return f"“{t[0]}”" if t else None
    if tool == "so_sanh_kich_ban":
        t = _titles(list(args.get("scenarios") or []))
        return " và ".join(f"“{x}”" for x in t) if t else None
    if tool == "gia_dinh":
        t = _titles(list(args.get("cung_luc") or []))
        return "cùng " + " và ".join(f"“{x}”" for x in t) if t else None
    return None


def says(tool: str, args: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """A call's three sentences, sent when it starts (its end carries no arguments): ``doing``, ``done``, ``failed``."""
    doing, done = SAYS.get(tool, ("Đang dùng một chức năng", "Đã dùng một chức năng"))
    d = _detail(tool, args or {})

    def put(s: str) -> str:
        if not d:
            return s
        return s.replace("trong tháng", d) if tool == "dong_tien" else f"{s}: {d}"

    return {"doing": put(doing), "done": put(done), "failed": "Không thực hiện được: " + put(doing)[5:].lower()}
