"""Check the living BRD repository (docs/brd): links, IDs, coverage, cited tests, statuses, sources.

    uv run python scripts/check_brd_docs.py [--brd PATH_TO_BRD_DOCX]

Checks, each an error when it fails:
- every relative link in docs/brd resolves to a file, and every #anchor to a heading of that file;
- every requirement ID defined in requirements/ has exactly one row in the traceability matrix, and every
  row's ID is defined; the BRD's 61 codes are all defined;
- every status in the matrix is in the vocabulary of README §4, and an ``implemented_verified`` row cites at
  least one test;
- every test cited anywhere as ``tests/<file>.py::<name>`` exists;
- the summary table of the matrix equals the counts of its rows;
- every FEAT-, SCR-, ADR-, Q- and DEF- id that is referenced is defined;
- the verbatim kit copies in sources/ still have their recorded SHA-256;
- every file under assets/ is registered in assets/README.md.
With ``--brd``, also: the file's SHA-256 is the registered one, and every BR/FR/NFR code in it is defined.

``tests/test_brd_docs.py`` runs it, so the suite fails when the documentation drifts from the code.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path
from typing import Dict, List, Set

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "brd"
MATRIX = DOCS / "requirements" / "requirements_traceability.md"
BRD_SHA256 = "5ea9d8da3e84bd196f8649a87a3b041ca9a1e01db109dca7f1570dd5a4cde1e3"
KIT_SHA256 = {
    "README.md": "5852cd48bf98ddf03c2a0a968f795912795eea09bb037a3b875cb9416b2ae9b6",
    "PROMPT_MASTER.md": "2048f37c88041d39deeccd236fd9012a487fa13f0992e9fa584fcae03e0d9440",
    "CHANGE_PROPOSAL.md": "6789e498e628867a5abdfc03ba761ba984a58d8c1d34d60fa714c76431348b15",
    "BRD_COVERAGE_AND_ACCEPTANCE.md": "89654529fa9e92a49edb283742fcc4a26e1ce746ff711fbe0d067ab68eb525d1",
    "PROMPT_FINANCIAL_INTELLIGENCE_GRAPH.md": "6aabac67d031811f6a42aa72247cbfbfe588b85c651e4d28b845b49cb1d332c3",
    "PROMPT_ONEWEALTH_COPILOT.md": "1ea19e1d7dc36cdd8717fedf8c01099489ec1c8964171f462a094477338ef60e",
}
# the BRD's own codes (BRD §4, §6, §15): 15 + 34 + 12 = 61
BRD_CODES = (
    [f"BR-{i:02d}" for i in range(1, 16)]
    + [f"FR-{n}" for n in (101, 102, 103, 104, 105, 201, 202, 203, 204)]
    + [f"FR-{n}" for n in range(301, 308)]
    + [f"FR-{n}" for n in range(401, 407)]
    + [f"FR-{n}" for n in (501, 502, 503, 601, 602, 603, 604, 701, 702, 703, 704, 801)]
    + [f"NFR-{i:02d}" for i in range(1, 13)]
)
STATUSES = (
    "implemented_verified",
    "implemented_unverified",
    "partially_implemented",
    "planned",
    "not_implemented",
    "blocked",
    "out_of_scope_demo",
    "not_applicable",
)
REQ_ID = r"(?:BRD-(?:BR-\d{2}|FR-\d{3}|NFR-\d{2}|KPI-\d{2}|RULE-[A-Z]+-\d{2})|(?:BRIEF|KIT|OWN)-[A-Z]+-\d{2})"
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)|!\[[^\]]*\]\(([^)\s]+)\)")
TEST_REF = re.compile(r"tests/(test_\w+\.py)::(test_\w+)")


def slug(heading: str) -> str:
    """GitHub's anchor for a heading: lower case, punctuation dropped, spaces to hyphens."""
    text = re.sub(r"`|\*|_(?=\W)|\[([^\]]*)\]\([^)]*\)", r"\1", heading.strip()).lower()
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path: Path) -> Set[str]:
    seen: Counter = Counter()
    out = set()
    in_code = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            in_code = not in_code
            continue
        m = None if in_code else re.match(r"#{1,6}\s+(.*)", line)
        if m:
            base = slug(m.group(1))
            out.add(base if not seen[base] else f"{base}-{seen[base]}")
            seen[base] += 1
    return out


def md_files() -> List[Path]:
    return sorted(p for p in DOCS.rglob("*.md") if "sources/redesign_kit" not in p.as_posix())


def check_links(errors: List[str]) -> None:
    cache: Dict[Path, Set[str]] = {}
    for md in md_files():
        text = md.read_text(encoding="utf-8")
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        for m in LINK.finditer(text):
            target = m.group(1) or m.group(2)
            if re.match(r"[a-z]+:", target):
                continue  # http:, https:, mailto:
            file_part, _, anchor = target.partition("#")
            dest = (md.parent / file_part).resolve() if file_part else md
            where = f"{md.relative_to(ROOT)} → {target}"
            if not dest.exists():
                errors.append(f"broken link: {where}")
                continue
            if anchor and dest.suffix == ".md":
                if dest not in cache:
                    cache[dest] = anchors(dest)
                if anchor not in cache[dest]:
                    errors.append(f"missing anchor: {where}")


def defined_requirements() -> Set[str]:
    ids: Set[str] = set()
    for md in (DOCS / "requirements").glob("*.md"):
        if md == MATRIX:
            continue
        for line in md.read_text(encoding="utf-8").splitlines():
            m = re.match(rf"(?:###\s+|\|\s*)({REQ_ID})\b", line)
            if m:
                ids.add(m.group(1))
    return ids


def matrix_rows() -> Dict[str, str]:
    """ID → the row's text, for every row of the matrix."""
    rows: Dict[str, str] = {}
    dup = []
    for line in MATRIX.read_text(encoding="utf-8").splitlines():
        m = re.match(rf"\|\s*({REQ_ID})\s*\|", line)
        if m:
            if m.group(1) in rows:
                dup.append(m.group(1))
            rows[m.group(1)] = line
    if dup:
        raise SystemExit(f"duplicate matrix rows: {dup}")
    return rows


def row_status(row: str) -> str:
    found = [c.strip() for c in row.split("|") if c.strip() in STATUSES]
    return found[0] if len(found) == 1 else ""


def tests_index() -> Dict[str, Set[str]]:
    out: Dict[str, Set[str]] = {}
    for f in (ROOT / "tests").glob("test_*.py"):
        out[f.name] = set(re.findall(r"^(?:async\s+)?def\s+(test_\w+)", f.read_text(encoding="utf-8"), re.M))
    return out


def check_requirements(errors: List[str], report: List[str]) -> None:
    defined = defined_requirements()
    rows = matrix_rows()
    for code in BRD_CODES:
        if f"BRD-{code}" not in defined:
            errors.append(f"BRD code {code} has no extracted requirement")
    for rid in sorted(defined - set(rows)):
        errors.append(f"{rid} is defined but has no matrix row")
    for rid in sorted(set(rows) - defined):
        errors.append(f"matrix row {rid} is not defined in requirements/")
    tests = tests_index()
    sets = {
        "BRD numbered (BR, FR, NFR)": r"BRD-(?:BR|FR|NFR)-",
        "BRD success metrics (KPI)": r"BRD-KPI-",
        "BRD rules (RULE)": r"BRD-RULE-",
        "Original brief (BRIEF)": r"BRIEF-",
        "Redesign kit (KIT)": r"KIT-",
        "Owner requests (OWN)": r"OWN-",
    }
    counts = {name: Counter() for name in sets}
    for rid, row in rows.items():
        status = row_status(row)
        if not status:
            errors.append(f"{rid}: no single valid status in its row")
            continue
        refs = TEST_REF.findall(row)
        if status == "implemented_verified" and not refs:
            errors.append(f"{rid}: implemented_verified without a cited test")
        for name, pattern in sets.items():
            if re.match(pattern, rid):
                counts[name][status] += 1
    # the summary table must match
    summary = {}
    for line in MATRIX.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] in sets and len(cells) == 2 + len(STATUSES):
            summary[cells[0]] = cells[1:]
    for name, c in counts.items():
        want = [str(sum(c.values()))] + [str(c[s]) for s in STATUSES]
        report.append(f"{name}: {dict(c)} (total {sum(c.values())})")
        if summary.get(name) != want:
            errors.append(f"summary row “{name}” is {summary.get(name)}, the rows say {want}")
    # every cited test exists, anywhere in docs/brd
    for md in md_files():
        for f, name in TEST_REF.findall(md.read_text(encoding="utf-8")):
            if name not in tests.get(f, set()):
                errors.append(f"{md.relative_to(ROOT)} cites a missing test: tests/{f}::{name}")


def check_references(errors: List[str]) -> None:
    feats = {p.name.split("-")[0] + "-" + p.name.split("-")[1] for p in (DOCS / "features").glob("FEAT-*.md")}
    screens = set(re.findall(r"SCR-(?:CL|RM|CIO|CMP|PRO)-\d{2}", (DOCS / "ux" / "screen_inventory.md").read_text()))
    adrs = {p.name[:8] for p in (DOCS / "decisions").glob("ADR-*.md")}
    oq = (DOCS / "requirements" / "open_questions.md").read_text(encoding="utf-8")
    questions = set(re.findall(r"^### (Q-\d{2})", oq, re.M))
    defects = set(re.findall(r"^\| (DEF-\d{2}) \|", (DOCS / "testing" / "regression_coverage.md").read_text(), re.M))
    for md in md_files():
        text = md.read_text(encoding="utf-8")
        rel = md.relative_to(ROOT)
        for f in set(re.findall(r"\bFEAT-(\d{2})\b", text)):
            if f"FEAT-{f}" not in feats:
                errors.append(f"{rel}: FEAT-{f} has no feature file")
        for s in set(re.findall(r"\bSCR-(?:CL|RM|CIO|CMP|PRO)-\d{2}\b", text)):
            if s not in screens:
                errors.append(f"{rel}: {s} is not in the screen inventory")
        for a in set(re.findall(r"\bADR-\d{4}\b", text)):
            if a not in adrs:
                errors.append(f"{rel}: {a} has no decision file")
        for q in set(re.findall(r"\bQ-\d{2}\b", text)):
            if q not in questions:
                errors.append(f"{rel}: {q} is not in open_questions.md")
        for d in set(re.findall(r"\bDEF-\d{2}\b", text)):
            if d not in defects:
                errors.append(f"{rel}: {d} is not in the defect list")


def check_sources_and_assets(errors: List[str]) -> None:
    kit = DOCS / "sources" / "redesign_kit_2026-10-15"
    for name, digest in KIT_SHA256.items():
        p = kit / name
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            errors.append(f"source copy changed or missing: {p.relative_to(ROOT)}")
    register = (DOCS / "assets" / "README.md").read_text(encoding="utf-8")
    for f in (DOCS / "assets").rglob("*"):
        if f.is_file() and f.name != "README.md" and f.name not in register:
            errors.append(f"asset not registered in assets/README.md: {f.relative_to(ROOT)}")


def check_brd(path: Path, errors: List[str], report: List[str]) -> None:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != BRD_SHA256:
        errors.append(f"the BRD's SHA-256 is {digest}, registered {BRD_SHA256}: a new version must be registered")
    xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
    text = re.sub(r"<[^>]+>", " ", xml)
    codes = set(re.findall(r"\b(BR-\d{2}|FR-\d{3}|NFR-\d{2})\b", text))
    missing = sorted(codes - set(BRD_CODES))
    if missing:
        errors.append(f"codes in the BRD not extracted: {missing}")
    report.append(f"BRD file checked: {len(codes)} codes, SHA-256 {'ok' if digest == BRD_SHA256 else 'CHANGED'}")


def check(brd: Path | None = None) -> tuple[List[str], List[str]]:
    errors: List[str] = []
    report: List[str] = []
    check_links(errors)
    check_requirements(errors, report)
    check_references(errors)
    check_sources_and_assets(errors)
    if brd is not None:
        check_brd(brd, errors, report)
    else:
        report.append("BRD file not given (--brd): its hash and codes were not checked")
    return errors, report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--brd", type=Path, help="path to the BRD .docx (it is not in git)")
    args = ap.parse_args()
    errors, report = check(args.brd)
    for line in report:
        sys.stdout.write(f"  {line}\n")
    for e in errors:
        sys.stdout.write(f"ERROR {e}\n")
    sys.stdout.write(f"{len(errors)} error(s)\n")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
