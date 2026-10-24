"""Configuration completes (BRD_COMPLETION_PLAN F4; FR-701, SEC-04/05, AI-02, MEAS-07, NFR-06): return assumptions,
forbidden phrases, consent, prompts and models as versioned configuration that the product reads; the fixed eval
set gating a prompt or model change; asset classes and analyst groups declared by configuration."""

import asyncio
import copy
import json
import re
from types import SimpleNamespace

import pytest
from test_views import agent, event, valid_view

from consolidate.ops import household
from control import config, roles
from engine import FactorModel, default_model
from engine.loadings import exposure
from procedural import goals
from scenarios import _sim
from views import agents, evalset, prompts, schema
from views import store as vstore

# -- the kinds, their owners and checks ----------------------------------------------------------


def test_the_new_kinds_have_the_brd_owners_and_two_people_for_prompts_and_models():
    k = config.KINDS
    assert (k["return_assumptions"]["owner"], k["return_assumptions"]["two_person"]) == ("cio", False)
    assert (k["forbidden_phrases"]["owner"], k["consent"]["owner"]) == ("cio", "cio")
    assert all(k[x]["owner"] == "admin" and k[x]["two_person"] and k[x]["eval"] for x in ("prompts", "models"))
    with pytest.raises(roles.Forbidden):
        config.propose("prompts", prompts.default(), "cio")
    with pytest.raises(ValueError, match="khóa"):
        config.propose("return_assumptions", {"growth": 0.07}, "cio")
    with pytest.raises(ValueError, match="hai mô hình khác nhau"):
        config.propose("models", {"cio": "x/a", "challenger": "x/a"}, "admin")
    bad = prompts.default()
    bad["synthesize"] = bad["synthesize"].replace("RE_SPREAD", "RE")
    with pytest.raises(ValueError, match="AI-05"):
        config.propose("prompts", bad, "admin")
    bad = prompts.default()
    del bad["lenses"]["credit"]
    with pytest.raises(ValueError, match="bốn nhóm"):
        config.propose("prompts", bad, "admin")


def test_version_1_of_the_prompts_is_the_text_the_agents_shipped_with():
    p = config.data("prompts")
    assert p == prompts.default() and config.active("prompts")["id"] == "CF-prompts-v1"
    text = prompts.fill(p["analyst"], guard=p["guard"], task=p["lenses"]["macro"]["task"])
    assert text.startswith("Bạn là nhóm phân tích vĩ mô và lãi suất") and "DỮ_LIỆU" in text and "<<" not in text


# -- what reads them -----------------------------------------------------------------------------


def test_the_return_assumptions_in_force_drive_the_life_scenarios():
    before = _sim.saving_for(1_000_000_000, 24)
    v = config.propose("return_assumptions", {**config.RETURNS, "safe": 0.0}, "cio", "lãi suất về 0")
    config.decide(v["id"], "approve", "cio")  # one person (SEC-05)
    assert _sim.R()["safe"] == 0.0 and _sim.saving_for(1_000_000_000, 24) == pytest.approx(1_000_000_000 / 24)
    assert before < 1_000_000_000 / 24


def test_the_cio_changes_the_forbidden_phrases_the_guard_reads():
    assert schema.forbidden_words("Đầu tư ngay kẻo lỡ") == []
    cur = config.data("forbidden_phrases")
    new = {"recommendation": cur["recommendation"] + ["đầu tư ngay"], "compliance": cur["compliance"] + ["nợ xấu"]}
    v = config.propose("forbidden_phrases", new, "cio")
    config.decide(v["id"], "approve", "cio")
    assert schema.forbidden_words("Đầu tư ngay kẻo lỡ") == ["đầu tư ngay"]
    assert goals.forbidden_words("Khách có nợ xấu") == ["nợ xấu"]


def test_the_consent_configuration_decides_who_the_family_view_reads():
    assert [m["id"] for m in household(client_id="C02", scope="family")()["waiting"]] == ["C02S"]
    cur = config.data("consent")
    v = config.propose("consent", {**cur, "require": {**cur["require"], "family_member": False}}, "cio")
    config.decide(v["id"], "approve", "cio2")
    got = household(client_id="C02", scope="family")()
    assert [m["id"] for m in got["members"]] == ["C02", "C02S"] and got["waiting"] == []


# -- prompts and models: two people and the eval set (AI-02, MEAS-07) -----------------------------


class EvalLLM:
    """Answers like a good model: each sample's view shocks its expected factor in its expected direction."""

    def __init__(self, model, sent, wrong=()):
        self.model, self.sent, self.wrong = model, sent, set(wrong)
        self.config = None  # not a real provider: the configured model is not rebuilt

    async def generate(self, messages, **kw):
        self.sent.append(messages)
        system, user = messages[0]["content"], messages[1]["content"]
        ids = sorted(set(re.findall(r"NW-E\d-\d", user)))
        if "Agent Phản biện" in system:
            text = json.dumps({"findings": [{"severity": "low", "title": "Thiếu nguồn", "detail": "…", "target": "x"}]})
        elif "tổng hợp" in system and not ids:  # a real event, not an eval sample
            text = json.dumps(valid_view(sorted(set(re.findall(r"NW-\d{6}", user)))), ensure_ascii=False)
        elif "tổng hợp" in system:
            sample = next(s for s in evalset.eval_set()["samples"] if ids[0].startswith(f"NW-{s['id']}-"))
            view = valid_view(ids)
            exp = sample["expect"]
            direction = exp["direction"]
            if sample["id"] in self.wrong:
                direction = "down" if direction == "up" else "up"
            view["scenarios"]["branches"][0]["core_shocks"] = [
                {"factor": exp["factor"], "direction": direction, "size": "M"}
            ]
            text = json.dumps(view, ensure_ascii=False)
        else:
            text = json.dumps({"factors": {}, "impacts": [], "note": "Không có tác động rõ."})
        return SimpleNamespace(
            model=self.model,
            choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=text))],
            usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
        )


@pytest.fixture
def live_eval(monkeypatch):
    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_CIO", "vendor/big-model")
    monkeypatch.setenv("LLM_MODEL_CHALLENGER", "vendor/small-model")
    sent = []
    llms = {"llm:cio": EvalLLM("vendor/big-model", sent), "llm:challenger": EvalLLM("vendor/small-model", sent)}
    import operonx.providers.ops._utils as hub_utils

    monkeypatch.setattr(hub_utils, "resolve_hub", lambda: SimpleNamespace(get=lambda key: llms[key]))
    return SimpleNamespace(sent=sent, llms=llms)


def test_a_prompt_change_runs_the_eval_set_and_needs_a_second_admin(live_eval):
    new = prompts.default()
    new["guard"] += " Viết ngắn gọn."
    v = config.propose("prompts", new, "admin", "Gọn hơn")
    with pytest.raises(ValueError, match="bộ đánh giá"):
        config.decide(v["id"], "approve", "admin2")  # not before the eval set ran
    done = asyncio.run(evalset.run_pending())
    assert done == [{"id": v["id"], "passed": True, "summary": done[0]["summary"]}]
    ev = config.get(v["id"])["eval"]
    assert ev["valid"] == 6 and ev["direction_hits"] == 6 and len(ev["runs"]) == 6
    # the eval ran the proposal's prompts, not the ones in force
    assert all("Viết ngắn gọn." in m[0]["content"] for m in live_eval.sent)
    nodes = [n for r in vstore.runs(v["id"]) for n in r["nodes"] if n["mode"] == "live"]
    assert nodes and all(n["prompt_version"] == v["id"] for n in nodes)
    with pytest.raises(roles.Forbidden):
        config.decide(v["id"], "approve", "admin")  # not by the one who proposed it
    config.decide(v["id"], "approve", "admin2")
    # a live run now uses the new prompts and records their version
    live_eval.sent.clear()
    r = agent(event("NHNN giữ nguyên lãi suất điều hành", "Lãi suất liên ngân hàng ổn định")["id"])
    assert all(n["prompt_version"] == v["id"] for n in r["runs"][0]["nodes"] if n["mode"] == "live")
    assert all("Viết ngắn gọn." in m[0]["content"] for m in live_eval.sent)


def test_a_proposal_that_fails_the_eval_set_cannot_be_approved(live_eval):
    live_eval.llms["llm:cio"].wrong = {"E1", "E2"}  # two directions wrong: 4/6 < 5
    v = config.propose("models", {"cio": "vendor/big-model", "challenger": "vendor/other-model"}, "admin")
    live_eval.llms["llm:challenger"].model = "vendor/other-model"
    asyncio.run(evalset.run_pending())
    ev = config.get(v["id"])["eval"]
    assert ev["passed"] is False and ev["direction_hits"] == 4 and ev["needed"] == 5
    with pytest.raises(ValueError, match="không qua bộ đánh giá"):
        config.decide(v["id"], "approve", "admin2")
    assert config.decide(v["id"], "reject", "admin2")["status"] == "REJECTED"


def test_without_the_ai_the_eval_set_does_not_run_and_nothing_is_approved():
    v = config.propose("models", {"cio": "a/one", "challenger": "a/two"}, "admin")
    asyncio.run(evalset.run_pending())
    ev = config.get(v["id"])["eval"]
    assert ev["status"] == "done" and not ev["passed"] and "AI đang tắt" in ev["summary"]
    with pytest.raises(ValueError):
        config.decide(v["id"], "approve", "admin2")


def test_the_models_in_force_are_the_configured_ones(live_eval):
    assert agents.models() == {"cio": "vendor/big-model", "challenger": "vendor/small-model"}  # version 1: .env
    with agents.use(models_data={"cio": "p/x", "challenger": "p/y"}):
        assert agents.models() == {"cio": "p/x", "challenger": "p/y"}
    assert agents.models()["cio"] == "vendor/big-model"


# -- NFR-06: an analyst group and an asset class declared by configuration ------------------------


def test_an_analyst_group_declared_in_the_prompts_runs_with_the_others():
    new = prompts.default()
    new["lenses"]["property"] = {
        "label": "Bất động sản chuyên sâu",
        "task": "thị trường nhà ở",
        "factors": ["VN_HOUSE"],
    }
    vid = config.propose("prompts", new, "admin")["id"]
    config.set_eval(vid, {"status": "done", "passed": True, "summary": "đạt (thử)"})
    config.decide(vid, "approve", "admin2")
    r = agent(event("Giá nhà ở Hà Nội tăng mạnh", "Nguồn cung căn hộ khan hiếm")["id"])
    names = [n["node"] for n in r["runs"][0]["nodes"]]
    assert "analyst:property" in names and "analyst:macro" in names


def test_an_asset_class_declared_in_the_factor_model_is_valued_by_its_loads():
    raw = copy.deepcopy(config.data("factor_model"))
    raw["loadings"]["classes"] = {
        "art": {"label": "Tranh nghệ thuật", "loads": {"VNINDEX": 0.3, "USDVND": 1.0}, "modelled": True}
    }
    m = FactorModel.from_dict(raw)
    e = exposure({"key": "k", "class": "art", "name": "Tranh", "value": 1_000_000_000, "kind": "asset"}, m, 3)
    assert e.loads == pytest.approx({"VNINDEX": 0.003, "USDVND": 0.01}) and e.modelled and "Tranh" in e.method
    raw["loadings"]["classes"]["stock"] = {"label": "x", "loads": {}}
    with pytest.raises(ValueError, match="built into"):
        FactorModel.from_dict(raw)
    del raw["loadings"]["classes"]["stock"]
    v = config.propose("factor_model", {k: v for k, v in raw.items()}, "cio")
    config.decide(v["id"], "approve", "cio2")
    assert schema.catalogue()["asset_class"]["art"] == "Tranh nghệ thuật" and default_model().loadings["classes"]
