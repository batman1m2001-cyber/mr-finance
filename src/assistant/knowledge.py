"""The assistant's knowledge (A5, assistant.md §6, ADR-0029): two operonx-kb collections, apart, in ``data/kb/``.

- **product** — the Vietnamese user guide (``docs/huong-dan/``): a file per role and ``chung.md`` for everyone, a
  section per page, its route in the heading; and, for everyone, the “Cách tính” formulas (``src/explain``) and the
  glossary, a section per metric or term. Synced on the first question of a process; an unchanged file is skipped.
  Tagged with its role, so a person's ``huong_dan`` reads their role's pages and the shared ones.
- **materials** — documents a person adds on the Bộ nhớ page (text, Markdown, HTML, Word, PowerPoint, Excel, PDF; at
  most 5 MB). Readable by their owner and, for a client, the RM assigned to them; deleted with the person's data.

Both are **lexical only** (FTS5, Vietnamese bigrams with accents folded): nothing is sent to an embedding service, so
a client's document never leaves. Measured on 24 product questions: the right page in the first three 24/24, first
20/24, MRR 0.91, 35 ms; with bge-m3 embeddings (OpenRouter) hybrid search scored 21/24 and MRR 0.93 for one second
more per question (docs/brd/testing/assistant_eval.md).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from operonx.core.registry import ResourceHub
from operonx_kb import CollectionSpec, KnowledgeBase
from operonx_kb.model.collection import AnalyzerSpec, ChunkerSpec, LexicalIndexSpec
from operonx_kb.registry import BlobStoreConfig, CatalogConfig, LexicalIndexConfig

from assistant import conversations as conv
from assistant.base import Ctx
from wealth.paths import ROOT

GUIDE = ROOT / "docs" / "huong-dan"
ROLE_OF = {"chung": "all", "khach-hang": "client", "rm": "rm", "cio": "cio", "tuan-thu": "compliance",
           "quan-tri": "admin", "chuyen-gia": "specialist"}  # fmt: skip
MAX_BYTES = 5 * 1024 * 1024
KINDS = (".txt", ".md", ".html", ".htm", ".docx", ".pptx", ".xlsx", ".pdf")
ROUTE = re.compile(r"#/[\w…/-]+")

_KBS: Dict[str, KnowledgeBase] = {}
_SYNCED: set = set()


def folder() -> Path:
    """Beside the state file: ``data/kb`` in production, the test's own folder in a test."""
    return conv.db_path().with_name("kb")


def kb() -> KnowledgeBase:
    """The knowledge base of this data folder, its resources registered for this process only (not written to
    resources.yaml) and its two collections created."""
    d = folder()
    tag = "mf" + hashlib.sha256(str(d).encode()).hexdigest()[:10]
    if tag not in _KBS:
        d.mkdir(parents=True, exist_ok=True)
        hub = ResourceHub.instance()
        keys = {"catalog": f"kb_catalog:{tag}", "blobs": f"kb_blob:{tag}", "lexical": f"kb_lexical:{tag}"}
        for key, config in (
            (keys["catalog"], CatalogConfig(path=str(d / "catalog.db"))),
            (keys["blobs"], BlobStoreConfig(root=str(d / "blobs"))),
            (keys["lexical"], LexicalIndexConfig(path=str(d / "lexical.db"))),
        ):
            if not hub.has(key):
                hub.register(config, key, persist=False)
        base = KnowledgeBase(catalog=keys["catalog"], blobs=keys["blobs"])
        analyzer = AnalyzerSpec(kind="vi", fold_diacritics=True)
        for name in ("product", "materials"):
            if base.catalog.get_collection(name) is None:
                base.create_collection(name, CollectionSpec(
                    chunker=ChunkerSpec(max_tokens=400, min_tokens=40),
                    lexical=LexicalIndexSpec(index=keys["lexical"], collection=name, analyzer=analyzer),
                ))  # fmt: skip
        _KBS[tag] = base
    return _KBS[tag]


# -- product ------------------------------------------------------------------------------------------------------


GENERATED = {"cach-tinh.md": "Cách tính", "thuat-ngu.md": "Thuật ngữ"}  # what a source says, by file


def _formulas() -> str:
    """The “Cách tính” catalogue as a guide: a section per metric, its name and its formula (src/explain)."""
    from explain import metrics  # noqa: F401  (fills the catalogue)
    from explain.catalogue import catalogue

    return "# Cách tính\n\n" + "".join(
        f"## {m['label']}\n\nCách tính {m['label']}: {m['formula']}\n\n" for m in catalogue().values()
    )


def _glossary() -> str:
    """The glossary (docs/brd/GLOSSARY.md) as a guide: a section per term."""
    rows = [r.strip().strip("|").split("|") for r in (ROOT / "docs" / "brd" / "GLOSSARY.md").read_text(
        encoding="utf-8").splitlines() if r.startswith("| ") and not r.startswith("| Term")]  # fmt: skip
    return "# Thuật ngữ\n\n" + "".join(f"## {c[0].strip()}\n\n{c[0].strip()}: {c[1].strip()} ({c[2].strip()})\n\n"
                                       for c in rows if len(c) >= 3)  # fmt: skip


async def sync_product() -> Dict[str, int]:
    """Every guide file in ``product``, and the formulas and the glossary as two more (a changed one replaced, an
    unchanged one skipped, a removed one deleted)."""
    base, out = kb(), {"new": 0, "update": 0, "skip": 0, "deleted": 0}
    files = {f.name: f for f in sorted(GUIDE.glob("*.md")) if f.stem in ROLE_OF}
    for name, f in files.items():
        got = await base.add("product", str(f), key=name, tags=[ROLE_OF[f.stem]], acl=["everyone"])
        out[got["action"]] += 1
    for name, text in (("cach-tinh.md", _formulas()), ("thuat-ngu.md", _glossary())):
        got = await base.add("product", data=text.encode(), name=name, key=name, tags=["ref"], acl=["everyone"])
        out[got["action"]] += 1
    for doc in base.documents("product"):
        if doc.key not in files and doc.key not in GENERATED:
            await base.delete("product", doc.key, purge=True)
            out["deleted"] += 1
    return out


def _route(heading: str, role: str) -> Optional[str]:
    m = ROUTE.search(heading or "")
    return m.group().replace("…", role) if m else None


async def guide(ctx: Ctx, query: str, k: int = 3) -> List[Dict[str, Any]]:
    """The guide's passages for ``query``, from the person's role's pages and the shared ones: each with its page,
    its route (when the heading names one) and the passage's own text; then the one formula or term that matches
    best. Two searches, not one: the 103 short formulas outranked the right page on 5 of the 24 product questions."""
    base = kb()
    if id(base) not in _SYNCED:  # once per process: a deploy restarts it, so a changed guide is read again
        await sync_product()
        _SYNCED.add(id(base))
    pages = await base.search("product", query, mode="lexical", k=k,
                              filter={"tags_any": [ctx.role, "all"], "acl_any": ["everyone"]})  # fmt: skip
    ref = await base.search(
        "product", query, mode="lexical", k=1, filter={"tags_any": ["ref"], "acl_any": ["everyone"]}
    )
    out = []
    for h in pages["hits"] + ref["hits"]:
        heading = (h.get("heading_path") or [""])[-1]
        out.append({"page": heading.split(" — ")[0], "route": _route(heading, ctx.role), "text": h["text"],
                    "file": h["key"]})  # fmt: skip
    return out


# -- materials ----------------------------------------------------------------------------------------------------


def readers(ctx: Ctx) -> List[str]:
    """Who may read what this person adds: themselves and, for a client, the RM assigned to them."""
    who = [f"owner:{conv.owner(ctx)}"]
    if ctx.role == "client" and ctx.client_id:
        from people import store

        rm = store.assigned_rm(ctx.client_id)
        if rm:
            who.append(f"rm:{rm}")
    return who


def principals(ctx: Ctx) -> List[str]:
    """What this person reads as: their own documents, and an RM's assigned clients' (of the client they picked)."""
    out = [f"owner:{conv.owner(ctx)}"]
    if ctx.role == "rm" and ctx.user:
        out.append(f"rm:{ctx.user}")
    return out


def _scope(ctx: Ctx) -> Dict[str, Any]:
    flt: Dict[str, Any] = {"acl_any": principals(ctx)}
    if ctx.role == "rm" and ctx.client_id:  # an RM reads the picked client's documents, and their own
        flt["tags_any"] = [f"client:{ctx.client_id}", f"owner:{conv.owner(ctx)}"]
    return flt


async def add_material(ctx: Ctx, name: str, data: bytes) -> Dict[str, Any]:
    name = Path(str(name or "")).name[:120]
    if not name or Path(name).suffix.lower() not in KINDS:
        raise ValueError(f"Chỉ nhận tệp {', '.join(KINDS)}")
    if not data:
        raise ValueError("Tệp trống")
    if len(data) > MAX_BYTES:
        raise ValueError("Tệp quá 5 MB")
    owner = conv.owner(ctx)
    tags = [f"owner:{owner}"] + ([f"client:{ctx.client_id}"] if ctx.role == "client" and ctx.client_id else [])
    got = await kb().add("materials", data=data, name=name, key=f"{owner}/{name}", title=name, tags=tags,
                         acl=readers(ctx), metadata={})  # fmt: skip
    return {"key": f"{owner}/{name}", "name": name, "action": got["action"]}


def materials(ctx: Ctx) -> List[Dict[str, Any]]:
    """The person's own documents (an RM also sees the picked client's), newest first."""
    mine = set(principals(ctx))
    scope = set(_scope(ctx).get("tags_any") or [])
    out = []
    for d in kb().documents("materials"):
        if not mine & set(d.acl or []):
            continue
        if scope and not scope & set(d.tags or []):
            continue
        out.append({"key": d.key, "name": d.key.split("/", 1)[-1], "own": d.key.startswith(conv.owner(ctx) + "/"),
                    "added": d.created_at.timestamp() if getattr(d, "created_at", None) else None})  # fmt: skip
    return sorted(out, key=lambda x: -(x["added"] or 0))


async def delete_material(ctx: Ctx, key: str) -> bool:
    """Only the owner deletes; the passages, the file and its versions go (purge), and the index with them."""
    if not str(key or "").startswith(conv.owner(ctx) + "/"):
        return False
    if kb().document("materials", key) is None:
        return False
    await kb().delete("materials", key, purge=True)
    return True


async def search_materials(ctx: Ctx, query: str, k: int = 4) -> List[Dict[str, Any]]:
    found = await kb().search("materials", query, mode="lexical", k=k, filter=_scope(ctx))
    return [{"name": h["key"].split("/", 1)[-1], "text": h["text"], "heading": (h.get("heading_path") or [""])[-1]}
            for h in found["hits"]]  # fmt: skip


async def forget_owner(ctx: Ctx) -> int:
    """Every document the person added, purged (with their data)."""
    n = 0
    for d in kb().documents("materials"):
        if d.key.startswith(conv.owner(ctx) + "/"):
            await kb().delete("materials", d.key, purge=True)
            n += 1
    return n


# -- the assistant's tools (registry) ---------------------------------------------------------------------------


def _question(args: Dict[str, Any]) -> str:
    from assistant.base import ToolFailed

    q = " ".join(str(args.get("q") or "").split())
    if len(q) < 2:
        raise ToolFailed("Cần một câu hỏi để tìm")
    return q[:300]


async def _guide(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    hits = await guide(ctx, _question(args))
    if not hits:
        return {"text": "Hướng dẫn sử dụng không có phần nào khớp câu hỏi này.", "data": {"passages": []}}
    text = " ".join(f"[{h['page']}] {' '.join(h['text'].split())[:600]}" for h in hits)
    out: Dict[str, Any] = {
        "text": "Theo hướng dẫn sử dụng: " + text,
        "data": {"passages": [{"page": h["page"], "route": h["route"]} for h in hits]},
        "sources": [f"{GENERATED.get(h['file'], 'Hướng dẫn sử dụng')} · {h['page']}" for h in hits],
    }
    first = next((h for h in hits if h["route"]), None)
    if first:
        out["evidence"] = {"label": first["page"], "route": first["route"]}
    return out


async def _materials(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    hits = await search_materials(ctx, _question(args))
    if not hits:
        return {"text": "Không thấy trong tài liệu bạn đã thêm.", "data": {"passages": 0}}
    text = " ".join(f"[{h['name']}] {' '.join(h['text'].split())[:600]}" for h in hits)
    return {"text": "Trong tài liệu của bạn: " + text, "data": {"passages": len(hits)},
            "sources": sorted({f"Tài liệu · {h['name']}" for h in hits})}  # fmt: skip


async def _web(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from assistant import web

    got = await web.search(ctx, _question(args))
    return {"text": got["text"], "data": {"query": got["query"], "results": len(got["sources"])},
            "sources": [s["url"] for s in got["sources"]], "cost_usd": got["cost_usd"]}  # fmt: skip


def _catalogue():
    from assistant.base import Param, Tool
    from control.roles import ROLE_LABELS

    everyone = tuple(ROLE_LABELS)
    return {
        t.name: t
        for t in [
            Tool("huong_dan", "cách dùng OneWealth: trang nào cho thấy gì, làm một việc trong ứng dụng thế nào, nút "
                 "hay chỉ số trên trang nghĩa là gì; trả về đoạn hướng dẫn kèm trang", everyone, _guide,
                 params={"q": Param(str, "câu hỏi về cách dùng, ngắn")}),
            Tool("tai_lieu", "tìm trong tài liệu người dùng đã tự thêm ở trang Bộ nhớ", everyone, _materials,
                 params={"q": Param(str, "từ khóa cần tìm, ngắn")}, page="bo-nho"),
            Tool("tim_tren_web", "tìm trên web cho câu hỏi ngoài dữ liệu của OneWealth (tin tức, quy định, kiến thức "
                 "chung); không dùng cho số liệu của người dùng; trả về câu trả lời kèm nguồn và mức độ chắc chắn",
                 everyone, _web, params={"q": Param(str, "câu hỏi cần tìm, không tên người, không số tài khoản")},
                 timeout=45.0, cost="paid"),
        ]
    }  # fmt: skip


CATALOGUE = _catalogue()
