"""statement_flow: the file → the model's reading (when AI is on) or the rules' → holdings."""

from operonx import END, START, graph
from operonx.core.ops import if_
from operonx.providers.ops import LLMOp

from statements.ops import (
    ai_mode,
    check_request,
    load_sample,
    model_failed,
    model_read,
    pick_items,
    read_file,
    rule_read,
    save_holdings,
)

READ_PROMPT = {
    "system": (
        "Bạn đọc sao kê ngân hàng / công ty chứng khoán của Việt Nam và trích ra các khoản tài sản. "
        "Trả lời bằng một khối JSON duy nhất: "
        '{{"holdings": [{{"type": "stock", "ticker": "MWG", "qty": 6000, "avg_price": 52000, "price": 68000}}, '
        '{{"type": "cash", "name": "Tiền", "balance": 120000000}}, '
        '{{"type": "deposit", "name": "Tiền gửi 12 tháng", "balance": 2000000000, "rate": 5.0, '
        '"maturity": "2027-03-15"}}]}}. '
        "Số tiền tính bằng đồng (VND), không dấu phân cách. Chỉ ghi những gì có trong sao kê."
    ),
    "user": "Tệp {filename}:\n\n{statement}",
}


@graph
def read_flow(filename, content):
    """A statement file → its items: the model's reading when AI is on, else the rules'; a model
    that fails or gives nothing usable falls back to the rules."""
    file = read_file(filename=filename, content=content)
    mode = ai_mode()
    model = LLMOp.of(
        resource="assistant",
        prompt=READ_PROMPT,
        fields=["holdings: list"],
        parser="json",
        filename=filename,
        statement=file["text"],
    )
    checked = model_read(
        holdings=model["holdings"],
        error=model["error"],
        kind=file["kind"],
        text=file["text"],
        rows=file["rows"],
    )
    oops = model_failed(kind=file["kind"], text=file["text"], rows=file["rows"])
    rules = rule_read(kind=file["kind"], text=file["text"], rows=file["rows"])
    picked = pick_items(
        institution=file["institution"],
        model_items=checked["items"],
        rule_items=rules["items"],
        fallback_items=oops["items"],
        model_method=checked["method"],
        rule_method=rules["method"],
        fallback_method=oops["method"],
    )
    model.on_error(oops)  # the model unreachable: the rules read it, the run goes on
    START >> file >> mode >> if_(mode["ai"] == True, model).else_(rules)  # noqa: E712
    model >> checked
    checked >> picked
    rules >> picked
    oops >> picked
    picked >> END


@graph
def statement_flow(client_id, filename, content):
    """A statement the client uploaded (POST /api/statement), read and kept as their tier-2
    holdings."""
    ask = check_request(client_id=client_id, filename=filename, content=content)
    got = read_flow(filename=ask["filename"], content=ask["content"])
    saved = save_holdings(
        client_id=ask["client_id"],
        filename=ask["filename"],
        institution=got["institution"],
        items=got["items"],
        method=got["method"],
    )
    START >> ask >> got >> saved >> END


@graph
def sample_flow(filename):
    """The eval's graph: a sample statement from data/samples, read (nothing is kept)."""
    sample = load_sample(filename=filename)
    got = read_flow(filename=filename, content=sample["content"])
    START >> sample >> got >> END
