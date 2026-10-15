"""The living BRD repository (docs/brd) stays consistent with itself and with the tests it cites."""

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "check_brd_docs", Path(__file__).resolve().parents[1] / "scripts" / "check_brd_docs.py"
)
checker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(checker)


def test_the_brd_repository_is_consistent():
    errors, _ = checker.check()
    assert errors == []


def test_every_brd_code_is_extracted():
    assert len(checker.BRD_CODES) == 61
    defined = checker.defined_requirements()
    assert all(f"BRD-{code}" in defined for code in checker.BRD_CODES)


def test_a_verified_row_needs_a_test_that_exists():
    rows = checker.matrix_rows()
    tests = checker.tests_index()
    for rid, row in rows.items():
        if checker.row_status(row) == "implemented_verified":
            refs = checker.TEST_REF.findall(row)
            assert refs, rid
            assert all(name in tests[f] for f, name in refs), rid
