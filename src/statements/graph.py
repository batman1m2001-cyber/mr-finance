"""intake_flow: what a client brings in. A statement: the file → the model's reading (when AI is on) or the rules' →
holdings. A declaration: one chat turn → the agent (or the rules) records it. read_flow is the statement's reading."""

from operonx import END, START, graph
from operonx.agents import AgentOp
from operonx.core.ops import if_
from operonx.providers.ops import LLMOp

from declare.agent import DECLARER, DECLARER_ONPREM
from declare.ops import agent_answer, chat_session, recorded, rule_declare
from declare.ops import ai_mode as declare_mode
from declare.ops import check_request as check_declare
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
from wealth.action import route

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
        resource=mode["resource"],  # llm:assistant (demo) or llm:onprem (BRD-NFR-08)
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
def intake_flow(action="statement", client_id=None, filename=None, content=None, message=None, session_id=None):
    """What a client brings in, one flow, the route picks its ``action`` (app/main.py `variants`; bodies.py has each
    route's request contract). ``statement`` (POST /api/statement): a statement the client uploaded, read and kept as
    their tier-2 holdings. ``declare`` (POST /api/declare): one chat turn, the agent records what the client says
    (when AI is on), or the rules do, as their tier-3 declarations. The turn said as it happens
    (POST /api/declare/stream) has doors and stays declare/graph.py declare_stream_flow."""
    which = route(action=action)

    ask = check_request(client_id=client_id, filename=filename, content=content)
    got = read_flow(filename=ask["filename"], content=ask["content"])
    saved = save_holdings(
        client_id=ask["client_id"],
        filename=ask["filename"],
        institution=got["institution"],
        items=got["items"],
        method=got["method"],
    )

    asked = check_declare(client_id=client_id, message=message, session_id=session_id)
    mode = declare_mode()
    agent = AgentOp.of(
        agent=DECLARER, input=asked["message"], session_id=asked["session_id"], deps=asked["client_id"], sessions=chat_session
    )
    onprem = AgentOp.of(
        agent=DECLARER_ONPREM,
        input=asked["message"],
        session_id=asked["session_id"],
        deps=asked["client_id"],
        sessions=chat_session,
    )
    said = agent_answer(
        client_id=asked["client_id"],
        message=asked["message"],
        output=agent["output"],
        status=agent["status"],
        error=agent["error"],
        onprem_output=onprem["output"],
        onprem_status=onprem["status"],
        onprem_error=onprem["error"],
    )
    rules = rule_declare(client_id=asked["client_id"], message=asked["message"])
    turn = recorded(
        client_id=asked["client_id"],
        since=mode["since"],
        ai_reply=said["reply"],
        rule_reply=rules["reply"],
        ai_method=said["method"],
        rule_method=rules["method"],
    )

    START >> which >> if_(which["action"] == "declare", asked).else_(ask)
    ask >> got >> saved >> END
    asked >> mode >> if_(mode["assistant"] == True, agent).if_(mode["onprem"] == True, onprem).else_(rules)  # noqa: E712
    agent >> said
    onprem >> said
    said >> turn
    rules >> turn
    turn >> END


@graph
def sample_flow(filename):
    """The eval's graph: a sample statement from data/samples, read (nothing is kept)."""
    sample = load_sample(filename=filename)
    got = read_flow(filename=filename, content=sample["content"])
    START >> sample >> got >> END
