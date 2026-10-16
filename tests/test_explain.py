"""The “cách tính” catalogue (BRD-NFR-11, BRD_REMAINING_PLAN G1): each metric names code that exists, each metric a
page uses is in the catalogue, and each metric in the catalogue is used by a page. The browser side — no figure
without its formula on any route — is tests/ui/test_how.py."""

import re
from pathlib import Path

from explain import metrics  # noqa: F401 — registers every metric
from explain.catalogue import catalogue

ROOT = Path(__file__).resolve().parents[1]
WEB = [p for p in (ROOT / "web").rglob("*.js")]
# the metric argument of n(text, metric, …), how(…), nAttrs(metric, …), howOn(node, metric, …), {metric: …}; the
# first argument may hold one level of parentheses
USE = re.compile(
    r'(?:\bhow|\bn)\((?:[^()]|\([^()]*\))*?,\s*"([\w.]+)"'
    r'|\bnAttrs\(\s*"([\w.]+)"|\bhowOn\(\w+,\s*"([\w.]+)"'
    r'|\bmetric:\s*"([\w.]+)"|\bmetric\s*\|\|\s*"([\w.]+)"\)'
)


def defines(path: Path, name: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".py":
        return re.search(rf"^\s*(?:async\s+)?(?:def|class)\s+{re.escape(name)}\b", text, re.M) is not None
    return re.search(rf"(?:function\s+{re.escape(name)}\b|(?:const|let)\s+{re.escape(name)}\s*=)", text) is not None


def test_every_metric_names_code_that_exists():
    bad = []
    for mid, m in catalogue().items():
        path, _, name = m["code"].partition("::")
        if not (ROOT / path).is_file() or not name or not defines(ROOT / path, name):
            bad.append(f"{mid}: {m['code']}")
    assert not bad, bad


def test_every_metric_has_a_label_a_formula_and_labelled_inputs():
    for mid, m in catalogue().items():
        assert m["label"] and len(m["formula"]) > 20, mid
        assert all(isinstance(v, str) and v for v in m["inputs"].values()), mid


def test_every_metric_a_page_uses_is_in_the_catalogue_and_every_one_is_used():
    used = {}
    for p in WEB:
        for hit in USE.finditer(p.read_text(encoding="utf-8")):
            used.setdefault(next(g for g in hit.groups() if g), p.name)
    assert len(used) > 60, sorted(used)  # the pattern still finds the calls
    unknown = {m: f for m, f in used.items() if m not in catalogue()}
    assert not unknown, unknown
    text = "\n".join(p.read_text(encoding="utf-8") for p in WEB)
    unused = [m for m in catalogue() if f'"{m}"' not in text]
    assert not unused, unused
