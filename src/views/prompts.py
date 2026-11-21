"""The agents' prompts as configuration (BRD-RULE-AI-02, F-D10): the ``prompts`` kind, owned by Admin, changed by
two people, and only after the fixed eval set passes on the proposal (MEAS-07, ``views.evalset``).

``DEFAULT`` is version 1 — the text the agents shipped with, kept as files in ``prompts/cio/``. Later versions are
this configuration kind's (the database, two people, the eval set), not the files'. A template names what it is
filled with between double angle brackets: ``<<guard>>`` (every prompt), ``<<task>>`` (the analyst), ``<<round>>``
(the debate).
Templates are not ``str.format`` strings because they show the JSON the model must answer with.

``lenses`` are the analyst groups: the four of the BRD (§8.1) are fixed in the agent graph and must stay; a lens
added here runs as a further analyst group (NFR-06: a new agent by configuration).
"""

from __future__ import annotations

import copy
from typing import Any, Dict

from operonx.prompts import prompt

from _shared.paths import ROOT

BUILT_IN_LENSES = ("macro", "equity", "credit", "other")


def _shipped(name: str) -> str:
    """The text the agents shipped with: ``prompts/cio/<name>.md`` (``operonx prompt show cio/<name>``)."""
    return prompt(f"cio/{name}", root=ROOT).text


DEFAULT: Dict[str, Any] = {
    "guard": _shipped("guard"),
    "lenses": {
        "macro": {
            "label": "Vĩ mô và lãi suất",
            "task": "vĩ mô và lãi suất: tiền, trái phiếu Chính phủ, tỷ giá (VN_RATE, VN_GOV, USDVND, US10Y, DXY)",
            "factors": ["VN_RATE", "VN_GOV", "USDVND", "US10Y", "DXY"],
        },
        "equity": {
            "label": "Cổ phiếu và quỹ",
            "task": "cổ phiếu và quỹ (VNINDEX, GLOBAL_EQ, FOREIGN_FLOW; ngành và mã trong danh mục)",
            "factors": ["VNINDEX", "GLOBAL_EQ", "FOREIGN_FLOW"],
        },
        "credit": {
            "label": "Tín dụng và bất động sản",
            "task": (
                "tín dụng và bất động sản: trái phiếu doanh nghiệp, BĐS, cổ phần tư nhân (RE_SPREAD, FIN_SPREAD, "
                "VN_HOUSE)"
            ),
            "factors": ["RE_SPREAD", "FIN_SPREAD", "VN_HOUSE"],
        },
        "other": {
            "label": "Hàng hóa và tài sản khác",
            "task": "hàng hóa và tài sản khác: vàng, tiền số, bảo hiểm (GOLD, SJC_GAP, BTC, BRENT)",
            "factors": ["GOLD", "SJC_GAP", "BTC", "BRENT"],
        },
    },
    "analyst": _shipped("analyst"),
    "debate": _shipped("debate"),
    "synthesize": _shipped("synthesize"),
    "challenge": _shipped("challenge"),
    "policy": _shipped("policy"),
}

NEEDS = {
    "analyst": ("<<guard>>", "<<task>>"),
    "debate": ("<<guard>>", "<<round>>"),
    "synthesize": ("<<guard>>",),
    "challenge": ("<<guard>>",),
}


def default() -> Dict[str, Any]:
    return copy.deepcopy(DEFAULT)


def fill(template: str, **values: Any) -> str:
    for k, v in values.items():
        template = template.replace(f"<<{k}>>", str(v))
    return template


def check(data: Any) -> None:
    """What a prompts version must hold (a refused proposal says why)."""
    from engine import default_model

    if not isinstance(data, dict):
        raise ValueError("lời nhắc là một bảng")
    for k in ("guard", *NEEDS):
        if not isinstance(data.get(k), str) or len(data[k].strip()) < 20:
            raise ValueError(f"thiếu lời nhắc {k!r} (ít nhất 20 ký tự)")
    for k, marks in NEEDS.items():
        missing = [m for m in marks if m not in data[k]]
        if missing:
            raise ValueError(f"lời nhắc {k!r} thiếu {', '.join(missing)}")
    if "policy" in data and not (  # the policy agent's (F9): optional in versions kept before it
        isinstance(data["policy"], str) and "DỮ_LIỆU" in data["policy"] and "nguyên văn" in data["policy"]
    ):
        raise ValueError("lời nhắc policy phải nói văn bản nằm giữa DỮ_LIỆU và HẾT_DỮ_LIỆU và đòi trích nguyên văn")
    if "DỮ_LIỆU" not in data["guard"]:
        raise ValueError("lời nhắc guard phải nói dữ liệu giữa DỮ_LIỆU và HẾT_DỮ_LIỆU không phải lệnh (§8.3)")
    if not ("VNINDEX" in data["synthesize"] and "RE_SPREAD" in data["synthesize"]):
        raise ValueError("lời nhắc synthesize phải giữ quy tắc nhánh căng thẳng có VNINDEX và RE_SPREAD (AI-05)")
    lenses = data.get("lenses")
    if not isinstance(lenses, dict):
        raise ValueError("thiếu bảng lenses (các nhóm phân tích)")
    missing = [x for x in BUILT_IN_LENSES if x not in lenses]
    if missing:
        raise ValueError(f"bốn nhóm phân tích của BRD phải còn: thiếu {', '.join(missing)}")
    ids = set(default_model().ids)
    for k, lens in lenses.items():
        if not (isinstance(k, str) and k.isidentifier() and isinstance(lens, dict)):
            raise ValueError(f"nhóm {k!r}: tên chỉ gồm chữ, số, gạch dưới")
        if not (lens.get("label") and lens.get("task") and isinstance(lens.get("factors"), list) and lens["factors"]):
            raise ValueError(f"nhóm {k}: cần label, task và factors")
        bad = [f for f in lens["factors"] if f not in ids]
        if bad:
            raise ValueError(f"nhóm {k}: yếu tố {', '.join(bad)} không có trong mô hình")
