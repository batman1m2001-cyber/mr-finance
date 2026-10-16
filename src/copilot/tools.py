"""The Copilot's tools: its thirteen, now kept in the assistant's registry (A1, ADR-0032) and unchanged here."""

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
)
TOOLS = {n: REGISTRY[n] for n in COPILOT}
