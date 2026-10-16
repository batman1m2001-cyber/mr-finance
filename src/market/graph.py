"""One graph per market job (app/main.py schedules them; `operonx run market_<kind>` runs one now)."""

from operonx import END, START, graph

from assistant.ops import follow_ups_market
from market.ops import (
    ask_load,
    backfill,
    crypto_bars,
    equity_bars,
    foreign_flow,
    fx_rates,
    gov_yields,
    propose_estimate,
    run_loads,
    sjc_gold,
    world_series,
)


@graph
def market_equity_flow(since=None, only=None, tick=None, at=None):
    """VN-Index and the stocks."""
    got = equity_bars(since=since, only=only)
    checked = follow_ups_market(job="market_equity", after=got["run"])  # the follow-ups on its series (A6)
    START >> got >> checked >> END
    got >> END  # the run stays the graph's answer


@graph
def market_flows_flow(since=None, only=None, tick=None, at=None):
    """Foreign flows on HOSE."""
    got = foreign_flow(since=since, only=only)
    checked = follow_ups_market(job="market_flows", after=got["run"])  # the follow-ups on its series (A6)
    START >> got >> checked >> END
    got >> END  # the run stays the graph's answer


@graph
def market_yields_flow(since=None, only=None, tick=None, at=None):
    """Government bond yields."""
    got = gov_yields(since=since, only=only)
    checked = follow_ups_market(job="market_yields", after=got["run"])  # the follow-ups on its series (A6)
    START >> got >> checked >> END
    got >> END  # the run stays the graph's answer


@graph
def market_fx_flow(since=None, only=None, tick=None, at=None):
    """USD/VND."""
    got = fx_rates(since=since, only=only)
    checked = follow_ups_market(job="market_fx", after=got["run"])  # the follow-ups on its series (A6)
    START >> got >> checked >> END
    got >> END  # the run stays the graph's answer


@graph
def market_world_flow(since=None, only=None, tick=None, at=None):
    """World markets."""
    got = world_series(since=since, only=only)
    checked = follow_ups_market(job="market_world", after=got["run"])  # the follow-ups on its series (A6)
    START >> got >> checked >> END
    got >> END  # the run stays the graph's answer


@graph
def market_crypto_flow(since=None, only=None, tick=None, at=None):
    """Crypto."""
    got = crypto_bars(since=since, only=only)
    checked = follow_ups_market(job="market_crypto", after=got["run"])  # the follow-ups on its series (A6)
    START >> got >> checked >> END
    got >> END  # the run stays the graph's answer


@graph
def market_gold_flow(since=None, only=None, tick=None, at=None):
    """SJC gold."""
    got = sjc_gold(since=since, only=only)
    checked = follow_ups_market(job="market_gold", after=got["run"])  # the follow-ups on its series (A6)
    START >> got >> checked >> END
    got >> END  # the run stays the graph's answer


@graph
def market_backfill_flow(since="2020-01-01", only=None):
    """History from ``since`` for every series."""
    got = backfill(since=since, only=only)
    START >> got >> END


@graph
def model_estimate_flow(by, end=None, note=""):
    """POST /api/model/estimate: the estimated model proposed as the next factor_model version."""
    done = propose_estimate(by=by, end=end, note=note)
    START >> done >> END


@graph
def market_load_ask_flow(by, since="2020-01-01"):
    """POST /api/market/load: an Admin queues a load of the history (Hệ thống)."""
    asked = ask_load(by=by, since=since)
    START >> asked >> END


@graph
def market_load_flow(tick=None, at=None):
    """The ``market_load`` job (every minute): the load an Admin asked for."""
    done = run_loads(tick=tick, at=at)
    START >> done >> END
