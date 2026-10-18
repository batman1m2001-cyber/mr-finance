"""The Copilot's tools: its thirteen, now kept in the assistant's registry (A1, ADR-0032) and unchanged here, and the
staff desks' reads (FEAT-41), so the keyword fallback answers each role's own questions (staff stress test D13)."""

from assistant.base import Ctx, Tool, ToolFailed, allowed  # noqa: F401 - the Copilot's names
from assistant.registry import REGISTRY
from assistant.tools import PAGES, USER, _vnd  # noqa: F401

COPILOT = (
    "tong_quan",
    "dong_tien",
    "chu_y",
    "muc_tieu",
    "tac_dong",
    "dieu_tra",
    "kich_ban",
    "hom_nay",
    "hop_tin",
    "tin_bi_giu",
    "mo_trang",
    "duyet_de_xuat",
    "lay_tin",
    # the staff desks' reads, no arguments (FEAT-41)
    "so_khach_hang",
    "ban_quyet_dinh",
    "phoi_nhiem",
    "lan_ap_dung",
    "do_chinh_xac",
    "su_kien",
    "canh_bao_he_thong",
    "agent_nen",
    "ban_chuyen_gia",
    "ban_kiem_soat",
    "chuoi_nhat_ky",
    "cau_hinh_cho_duyet",
    "van_hanh",
)
TOOLS = {n: REGISTRY[n] for n in COPILOT}
