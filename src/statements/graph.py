"""statement_flow: the file → the model's reading (when AI is on) or the rules' → holdings."""

from operonx import END, START, graph
from operonx.app.serve import egress, ingress
from operonx.core.ops import if_
from operonx.providers.ops import LLMOp

from statements.ops import (
    ai_mode,
    model_failed,
    model_read,
    read_file,
    read_request,
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
def statement_flow(client_id, filename, content):
    """A statement the client uploaded, read and kept as their tier-2 holdings."""
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
    saved = save_holdings(
        client_id=client_id,
        filename=filename,
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
    checked >> saved
    rules >> saved
    oops >> saved
    saved >> END


@graph
def statement_api():
    """POST {client_id, filename, content: base64} → what was read."""
    req = ingress()
    ask = read_request(item=req["item"])
    read = statement_flow(client_id=ask["client_id"], filename=ask["filename"], content=ask["content"])
    out = egress(item=read["read"])
    START >> req >> ask >> read >> out >> END
