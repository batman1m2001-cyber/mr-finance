"""The data catalog the model reads before it writes a ``truy_van`` query (docs/ASSISTANT_DATA_PLAN.md §3.3, OWN-DA-04).

Generated from the room (:data:`assistant.dataroom.TABLES`: which tables a role has, their columns and types) and
hand-written files in ``catalog/``: ``tables.md`` (what each table and column means, its unit and allowed values),
``rules.md`` (time and search rules every role shares) and ``<role>.md`` (the business's definitions and question →
SQL examples). Admin reads Compliance's file: the same tables."""

import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

from assistant.dataroom import TABLES, tables_for

HERE = Path(__file__).parent / "catalog"
FILE = {"cio": "cio", "rm": "rm", "client": "client", "compliance": "compliance", "admin": "compliance"}
_TABLE = re.compile(r"^## (\w+)\n(.*?)(?=^## |\Z)", re.S | re.M)
_COLUMN = re.compile(r"^- `(\w+)`: (.+)$", re.M)
_EXAMPLE = re.compile(r"^Hỏi: (.+?)\n```sql\n(.+?)\n```", re.S | re.M)


def _read(name: str) -> str:
    text = (HERE / f"{name}.md").read_text(encoding="utf-8")
    return re.sub(r"<!--.*?-->\n?", "", text, flags=re.S).strip()


@lru_cache(maxsize=1)
def docs() -> Dict[str, Tuple[str, Dict[str, str]]]:
    """``{table: (what it holds, {column: meaning})}`` from ``tables.md``."""
    out = {}
    for name, body in _TABLE.findall(_read("tables")):
        about = "\n".join(line for line in body.strip().splitlines() if not line.startswith("- ")).strip()
        out[name] = (about, dict(_COLUMN.findall(body)))
    return out


def examples(role: str) -> List[Tuple[str, str]]:
    """The role's (question, SQL) examples."""
    return [(q.strip(), sql.strip()) for q, sql in _EXAMPLE.findall(_read(FILE[role]))]


@lru_cache(maxsize=None)
def catalog(role: str) -> str:
    """What the model knows about the role's room: the rules, each table with its columns (name, type, meaning),
    then the role's definitions and examples. Empty for a role without a room."""
    if role not in FILE:
        return ""
    meanings = docs()
    parts = [_read("rules"), "", "# Bảng"]
    for t in tables_for(role):
        about, cols = meanings[t.name]
        parts.append(f"## {t.name}: {about}")
        parts += [f"- {c} {kind.lower()}: {cols[c]}" for c, kind in t.columns]
    parts += ["", _read(FILE[role])]
    return "\n".join(parts)


def undocumented() -> List[str]:
    """``table.column`` names of the room missing from ``tables.md``, and names there that the room has not."""
    meanings = docs()
    out = [f"{t}" for t in meanings if t not in TABLES]
    for name, t in TABLES.items():
        cols = meanings.get(name, ("", {}))[1]
        have = [c for c, _ in t.columns]
        out += [f"{name}.{c}" for c in have if c not in cols]
        out += [f"{name}.{c}" for c in cols if c not in have]
    return out
