"""Write data/people/staff.json: the seed of the staff in the people table (src/people).

Everyone who works on a family, in one list:
- the staff who sign in: CIO and Admin users (two of each: the second is the second pair of eyes) and the RMs.

There is no Compliance or specialist user (OWN-FB-18): the CIO took Compliance's duties, four eyes kept, and an
action recommendation is the RM's alone.

The RMs who sign in are the RMs on the families' teams, so “your RM” and the RM user are the same person.
Names, e-mails, phones and offices are the advisory record's (scripts/make_advisory.py). Each family's team is
its RM. All mock.
Deterministic.

    uv run python scripts/make_people.py
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "people" / "staff.json"

_spec = importlib.util.spec_from_file_location("make_advisory", ROOT / "scripts" / "make_advisory.py")
adv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adv)

D = adv.DOMAIN
RM_IDS = {"hcm": "rm01", "private": "rm02", "hn": "rm03"}
HOURS = "8:00 – 18:00, thứ Hai – thứ Bảy"


def staff() -> list:
    office = {"hcm": adv.OFFICE_HCM, "hn": adv.OFFICE_HN, "private": adv.OFFICE_HCM}
    out = [
        {
            "id": "cio",
            "role": "cio",
            "name": "Trần Quang Huy",
            "title": "Giám đốc đầu tư (CIO)",
            "email": f"huy.tran@{D}",
        },
        {"id": "cio2", "role": "cio", "name": "Lê Thu Hà", "title": "Phó giám đốc đầu tư", "email": f"ha.le@{D}"},
    ]
    for key, rid in RM_IDS.items():
        rm = adv.RMS[key]
        out.append(
            {
                "id": rid,
                "role": "rm",
                "name": rm["name"],
                "title": "Chuyên viên quan hệ khách hàng",
                "title_en": "Relationship manager",
                "email": rm["email"],
                "phone": rm["phone"],
                "office": office[key],
                "hours": HOURS,
            }
        )
    out += [
        {"id": "admin", "role": "admin", "name": "Quản trị demo", "title": "Quản trị", "email": f"admin@{D}"},
        {
            "id": "admin2",
            "role": "admin",
            "name": "Đỗ Minh Khôi",
            "title": "Quản trị (người duyệt thứ hai)",
            "email": f"admin2@{D}",
        },
    ]
    return out


def teams() -> dict:
    return {cid: {"rm": RM_IDS[c["rm"]]} for cid, c in adv.CLIENTS.items()}


def main() -> None:
    out = {
        "note": "Seed of the staff in the people table (src/people): mock people, loaded into an empty database and "
        "on demo reset, never read at request time. Written by scripts/make_people.py.",
        "staff": staff(),
        "teams": teams(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
