"""The declaring agent (declare_flow, and its stream): records what the client says with its tools, answers like a
person in a line or two, and asks back only what it cannot record without — with a form when several things are
missing."""

from operonx.agents import Agent, Model, UsageLimits

from declare.tools import TOOLS
from operonx.prompts import prompt
from _shared.paths import ROOT

DECLARER = Agent(
    name="declarer",
    model=Model("assistant", deadline=45),
    instructions=(
        prompt("declare/agent", root=ROOT).text
    ),
    tools=TOOLS,
    limits=UsageLimits(turns=6, tool_calls=12),
)
# the same agent on the bank's own model, for client_ai = onprem (BRD-NFR-08, control/barrier.py)
DECLARER_ONPREM = DECLARER.clone(model=Model("onprem", deadline=45))
