"""Write the sample statements under data/samples/: what a client would upload in the demo.

- vps_C01.csv   a VPS securities statement (CSV)
- ssi_C05.xlsx  an SSI securities statement (Excel)
- vcb_C04.pdf   a Vietcombank deposit statement (PDF)

The PDF is written by hand (a few text lines, no font embedding), so its text is plain ASCII, as
many bank exports are.

    uv run python scripts/make_samples.py
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

OUT = Path(__file__).resolve().parents[1] / "data" / "samples"

VPS_CSV = """CONG TY CO PHAN CHUNG KHOAN VPS
SAO KE TAI SAN,Ngay 30/09/2026
Chu tai khoan,NGUYEN MINH KHOA
So tai khoan,123C456789
Ma CK,So luong,Gia von,Gia thi truong,Gia tri thi truong
MWG,6000,52000,68000,408000000
SSI,15000,25000,33000,495000000
Tien,,,,120000000
"""

SSI_ROWS = [
    ["CONG TY CO PHAN CHUNG KHOAN SSI"],
    ["BAO CAO DANH MUC", "Ngay 30/09/2026"],
    ["Khach hang", "VU NGOC ANH"],
    [],
    ["Ma chung khoan", "Khoi luong", "Gia binh quan", "Gia hien tai", "Gia tri"],
    ["HPG", 5000, 24000, 27500, 137500000],
    ["MBB", 4000, 22000, 24500, 98000000],
    ["Tien mat", None, None, None, 50000000],
]

VCB_LINES = [
    "NGAN HANG TMCP NGOAI THUONG VIET NAM (VIETCOMBANK)",
    "SAO KE TIEN GUI - Ngay 30/09/2026",
    "Khach hang: DO THI HANH",
    "So tai khoan: 0071000123456",
    "Loai: Tien gui co ky han 12 thang | So du: 2.000.000.000 VND | Lai suat: 5,0%/nam | Ngay dao han: 15/03/2027",
    "Loai: Tai khoan thanh toan | So du: 85.000.000 VND",
]


def pdf(lines: list[str]) -> bytes:
    """A one-page PDF with these lines of text in Helvetica."""
    esc = lambda s: s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")  # noqa: E731
    body = "BT /F1 10 Tf 40 800 Td 14 TL " + " ".join(f"({esc(t)}) Tj T*" for t in lines) + " ET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(body)} >>\nstream\n{body}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n".encode("latin-1")
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{o:010d} 00000 n \n" for o in offsets).encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "vps_C01.csv").write_text(VPS_CSV, encoding="utf-8")
    wb = Workbook()
    ws = wb.active
    ws.title = "Danh muc"
    for row in SSI_ROWS:
        ws.append(row)
    wb.save(OUT / "ssi_C05.xlsx")
    (OUT / "vcb_C04.pdf").write_bytes(pdf(VCB_LINES))


if __name__ == "__main__":
    main()
