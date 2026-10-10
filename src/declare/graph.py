"""declare_flow: one chat turn — the agent records what the client says (when AI is on), or the
rules do — and what the turn added to their profile."""

from operonx import END, START, graph
from operonx.agents import Agent, AgentOp, Model, UsageLimits
from operonx.core.ops import if_

from declare.ops import agent_answer, ai_mode, chat_session, check_request, recorded, rule_declare
from declare.tools import TOOLS

DECLARER = Agent(
    name="declarer",
    model=Model("assistant", deadline=45),
    instructions=(
        "Bạn là trợ lý của Mr. Finance, giúp khách hàng tự khai tài sản và hoàn cảnh gia đình mà "
        "ngân hàng chưa thấy: bất động sản ngoài hệ thống, vàng, cổ phần doanh nghiệp, bảo hiểm, "
        "khoản nợ bên ngoài, người phụ thuộc, thu nhập khác. Với mỗi điều khách nói, gọi đúng công cụ "
        "để ghi lại; tiền tính bằng tỷ hoặc triệu như khách nói. Không đoán con số khách không nói. "
        "Sau khi ghi, trả lời ngắn gọn bằng tiếng Việt: liệt kê những gì đã ghi và hỏi thêm thông tin "
        "còn thiếu (ví dụ diện tích hoặc giá trị hiện tại của một căn nhà). Không đưa lời khuyên đầu tư."
    ),
    tools=TOOLS,
    limits=UsageLimits(turns=6, tool_calls=12),
)


@graph
def declare_flow(client_id, message, session_id=None):
    """One message from the client (POST /api/declare), recorded as their tier-3 declarations."""
    ask = check_request(client_id=client_id, message=message, session_id=session_id)
    client_id, message, session_id = ask["client_id"], ask["message"], ask["session_id"]
    mode = ai_mode()
    agent = AgentOp.of(agent=DECLARER, input=message, session_id=session_id, deps=client_id, sessions=chat_session)
    said = agent_answer(
        client_id=client_id,
        message=message,
        output=agent["output"],
        status=agent["status"],
        error=agent["error"],
    )
    rules = rule_declare(client_id=client_id, message=message)
    turn = recorded(
        client_id=client_id,
        since=mode["since"],
        ai_reply=said["reply"],
        rule_reply=rules["reply"],
        ai_method=said["method"],
        rule_method=rules["method"],
    )
    START >> ask >> mode >> if_(mode["ai"] == True, agent).else_(rules)  # noqa: E712
    agent >> said >> turn
    rules >> turn
    turn >> END
