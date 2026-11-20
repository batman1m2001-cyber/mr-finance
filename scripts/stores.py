"""Which store each op reads and writes: derived from the SQL the op reaches, and held equal to what it declares.

    python scripts/stores.py            # check: every @op's reads=/writes= is what its code reaches (exit 1 if not)
    python scripts/stores.py --write    # write the declarations into the @op decorators
    python scripts/stores.py --tables   # the tables no store lists, and the ops that reach them

A store is a name for a group of tables (`[stores.<name>] tables = [...]` in operonx.toml). An op reaches a table when
its function, or a function it calls in this project (followed through imports), holds SQL naming it: `insert into`,
`update`, `delete from` are writes, `from` / `join` reads. An op that writes a store is not also listed as reading it.
Tables in no store (sign-in, the audit log, counters, settings) are every flow's and are not declared.

The studio's project picture draws `flow → store → flow` from the declarations (operonx ≥ 1.39, `@op(reads=, writes=)`).
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]
BASES = [ROOT / "src", ROOT]
SKIP_DIRS = {
    ".venv",
    "node_modules",
    ".git",
    "tests",
    "__pycache__",
    ".operonx",
    "web",
    "data",
    "datasets",
    "docs",
    "scripts",
}
WRITES = re.compile(
    r"\b(?:insert\s+(?:or\s+\w+\s+)?into|replace\s+into|update|delete\s+from)\s+([a-z_][a-z0-9_]*)", re.I
)
READS = re.compile(r"\b(?:from|join)\s+([a-z_][a-z0-9_]*)", re.I)
IS_SQL = re.compile(r"\b(select|insert|update|delete|replace)\b[\s\S]*\b(from|into|set)\b", re.I)


def load_modules() -> dict:
    mods = {}
    for base in BASES:
        for path in sorted(base.rglob("*.py")):
            rel = path.relative_to(base)
            if set(rel.parts[:-1]) & SKIP_DIRS or (base == ROOT and rel.parts[0] == "src"):
                continue
            name = ".".join(rel.with_suffix("").parts)
            name = name[: -len(".__init__")] if name.endswith(".__init__") else name
            mods.setdefault(name, (path, ast.parse(path.read_text(encoding="utf-8"))))
    return mods


def store_of_table() -> dict:
    table = tomllib.loads((ROOT / "operonx.toml").read_text(encoding="utf-8")).get("stores") or {}
    return {t: name for name, spec in table.items() for t in spec.get("tables") or []}


def derive() -> tuple[dict, dict]:
    """({'module:fn': (path, node, {table: 'r' | 'w'})} for every @op, {table: ...} the same for tables in no store)."""
    mods, funcs, imports = load_modules(), {}, {}
    for m, (_, tree) in mods.items():
        imp = {}
        for n in tree.body:
            if isinstance(n, ast.ImportFrom) and n.module and not n.level:
                for a in n.names:
                    full = f"{n.module}.{a.name}"
                    imp[a.asname or a.name] = ("mod", full) if full in mods else ("fn", n.module, a.name)
            elif isinstance(n, ast.Import):
                for a in n.names:
                    if a.name in mods:
                        imp[a.asname or a.name.split(".")[0]] = ("mod", a.name)
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs[(m, n.name)] = n
        imports[m] = imp

    def own(node) -> set:
        out = set()
        for x in ast.walk(node):
            if isinstance(x, ast.Constant) and isinstance(x.value, str) and IS_SQL.search(x.value):
                w = {t.lower() for t in WRITES.findall(x.value)}
                out |= {(t, "w") for t in w} | {(t.lower(), "r") for t in READS.findall(x.value) if t.lower() not in w}
        return out

    memo: dict = {}

    def reach(key, stack=()) -> set:
        if key in memo:
            return memo[key]
        if key in stack or key not in funcs:
            return set()
        m, node, out = key[0], funcs[key], set()
        out |= own(node)
        for x in ast.walk(node):
            if not isinstance(x, ast.Call):
                continue
            f, target = x.func, None
            if isinstance(f, ast.Name):
                target = (m, f.id) if (m, f.id) in funcs else None
                i = imports[m].get(f.id)
                if i and i[0] == "fn":
                    target = (i[1], i[2])
            elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
                i = imports[m].get(f.value.id)
                if i and i[0] == "mod":
                    target = (i[1], f.attr)
            if target:
                out |= reach(target, stack + (key,))
        memo[key] = out
        return out

    ops = {}
    for (m, fn), node in sorted(funcs.items()):
        if any(ast.unparse(d).split("(")[0].split(".")[-1] == "op" for d in node.decorator_list):
            kinds: dict = {}
            for table, kind in reach((m, fn)):
                kinds[table] = "w" if kind == "w" or kinds.get(table) == "w" else "r"
            ops[f"{m}:{fn}"] = (mods[m][0], node, kinds)
    return ops


def wanted(kinds: dict, stores: dict) -> tuple[list, list]:
    writes = sorted({stores[t] for t, k in kinds.items() if k == "w" and t in stores})
    reads = sorted({stores[t] for t in kinds if t in stores} - set(writes))
    return reads, writes


def declared(node) -> tuple[list, list, ast.expr]:
    for d in node.decorator_list:
        if ast.unparse(d).split("(")[0].split(".")[-1] == "op":
            got = {"reads": [], "writes": []}
            for kw in d.keywords if isinstance(d, ast.Call) else []:
                if kw.arg in got:
                    v = ast.literal_eval(kw.value)
                    got[kw.arg] = sorted([v] if isinstance(v, str) else v)
            return got["reads"], got["writes"], d
    raise AssertionError("not an op")


def rewrite(path: Path, edits: list) -> None:
    """Each edit: (decorator node, reads, writes). Bottom-up, so line numbers hold."""
    lines = path.read_text(encoding="utf-8").split("\n")
    for d, reads, writes in sorted(edits, key=lambda e: -e[0].lineno):
        kept = [
            f"{kw.arg}={ast.unparse(kw.value)}"
            for kw in (d.keywords if isinstance(d, ast.Call) else [])
            if kw.arg not in ("reads", "writes")
        ]
        for key, names in (("reads", reads), ("writes", writes)):
            if names:
                kept.append(f"{key}={names[0]!r}" if len(names) == 1 else f"{key}={names!r}")
        text = (
            "@" + ast.unparse(d.func if isinstance(d, ast.Call) else d) + (f"({', '.join(kept)})" if kept else "")
        ).replace("'", '"')
        indent = lines[d.lineno - 1][: len(lines[d.lineno - 1]) - len(lines[d.lineno - 1].lstrip())]
        lines[d.lineno - 1 : d.end_lineno] = [indent + text]
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list) -> int:
    stores, ops = store_of_table(), derive()
    out = sys.stdout.write
    if "--tables" in argv:
        loose: dict = {}
        for name, (_, _, kinds) in ops.items():
            for t in kinds:
                if t not in stores:
                    loose.setdefault(t, []).append(name)
        for t in sorted(loose):
            out(f"{t}: {len(loose[t])} ops\n")
        return 0
    wrong, edits = [], {}
    for name, (path, node, kinds) in ops.items():
        reads, writes = wanted(kinds, stores)
        has_r, has_w, dec = declared(node)
        if (reads, writes) != (has_r, has_w):
            wrong.append(
                f"{path.relative_to(ROOT)}:{node.lineno} {name.split(':')[1]}: reaches reads={reads} writes={writes}, "
                f"declares reads={has_r} writes={has_w}"
            )
            edits.setdefault(path, []).append((dec, reads, writes))
    if "--write" in argv:
        for path, list_ in edits.items():
            rewrite(path, list_)
        out(f"{len(wrong)} ops rewritten in {len(edits)} files\n")
        return 0
    for line in wrong:
        out(line + "\n")
    out(
        f"{len(ops)} ops, {len(wrong)} whose stores are not what they declare"
        + (" (python scripts/stores.py --write)\n" if wrong else "\n")
    )
    return 1 if wrong else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
