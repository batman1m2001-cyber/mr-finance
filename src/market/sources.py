"""The outside market sources, one adapter each (BRD_COMPLETION_PLAN F1, F-D2; probed 2026-10-16).

An adapter asks one public source for one series over a date range and returns ``(date, value)`` points in the
series' unit, and the URL it asked. It reaches the network only through ``http`` (a :class:`Request` → bytes
function), so the tests replace the network with responses recorded from each source. None of these sources needs
an account; they are unofficial, so each series names a fallback (data/market_sources.json, the ``price_sources``
configuration) and every stored point keeps its source and URL.

- ``vndirect``: VNDirect's chart API, daily bars since 2020 (stocks in thousands of VND, indexes in points).
- ``vietcap``: Vietcap's OHLC chart (VND), the fallback for the same symbols.
- ``msn``: MSN Finance's chart API, world series (gold, Brent, ACWI, S&P 500, US 10-year, FX); its anonymous key
  is the one MSN's own public page configuration carries.
- ``binance``: Binance daily klines (BTC, ETH in USDT).
- ``vcb``: Vietcombank's rate table by date (USD transfer rate).
- ``pnj``: PNJ's gold price history, which carries SJC bars (VND per lượng).
- ``hnx``: HNX's government bond yield curve by date (annual spot rate per tenor; needs an unverified TLS
  context, the site serves an incomplete chain).
- ``wgb``: worldgovernmentbonds.com, Vietnam 10-year since 2016 (fallback for the HNX 10-year).
- ``cafef``: cafef's foreign trading history for HOSE (net value, VND).
"""

from __future__ import annotations

import json
import math
import re
import ssl
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional, Tuple

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
MAX_BYTES = 8 * 1024 * 1024

Point = Tuple[str, float]


@dataclass
class Request:
    url: str
    method: str = "GET"
    body: Optional[bytes] = None
    headers: Dict[str, str] = field(default_factory=dict)
    insecure: bool = False  # HNX only: its certificate chain is incomplete


Http = Callable[[Request], bytes]


@dataclass
class Fetched:
    points: List[Point]
    url: str


class SourceError(RuntimeError):
    """A source answered, but not with what it should have."""


def http(req: Request, timeout: float = 25.0) -> bytes:
    """The network: one request, a browser user agent, at most 8 MB."""
    r = urllib.request.Request(req.url, data=req.body, method=req.method, headers={"User-Agent": UA, **req.headers})
    ctx = ssl._create_unverified_context() if req.insecure else None  # noqa: S323 — HNX's chain, read-only data
    with urllib.request.urlopen(r, timeout=timeout, context=ctx) as resp:  # noqa: S310 — fixed https hosts
        return resp.read(MAX_BYTES)


def _json(raw: bytes):
    try:
        return json.loads(raw)
    except ValueError as exc:
        raise SourceError(f"không phải JSON: {raw[:80]!r}") from exc


def _unix(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def _day(ts: float) -> str:
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).date().isoformat()


def _num(text: str) -> float:
    """A number written the Vietnamese way (``3,89`` or ``146.500``) or the English way."""
    s = str(text).strip()
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    elif "," in s:
        s = s.replace(",", "")
    return float(s)


def _within(points: List[Point], start: date, end: date) -> List[Point]:
    a, b = start.isoformat(), end.isoformat()
    out: Dict[str, float] = {}
    for d, v in points:
        if a <= d <= b and v is not None and math.isfinite(v):
            out[d] = v  # one point a day: the last one given
    return sorted(out.items())


# -- Vietnamese equities ----------------------------------------------------------------------


def vndirect(symbol: str, start: date, end: date, get: Http = http, scale: float = 1.0) -> Fetched:
    q = urllib.parse.urlencode(
        {"resolution": "D", "symbol": symbol, "from": _unix(start), "to": _unix(end + timedelta(days=1))}
    )
    url = f"https://dchart-api.vndirect.com.vn/dchart/history?{q}"
    d = _json(get(Request(url)))
    if d.get("s") not in ("ok", "no_data"):
        raise SourceError(f"vndirect {symbol}: {d.get('s')!r}")
    pts = [(_day(t), float(c) * scale) for t, c in zip(d.get("t") or [], d.get("c") or [])]
    return Fetched(_within(pts, start, end), url)


def vietcap(symbol: str, start: date, end: date, get: Http = http, scale: float = 1.0) -> Fetched:
    url = "https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart"
    days = (end - start).days + 10
    body = {"timeFrame": "ONE_DAY", "symbols": [symbol], "to": _unix(end + timedelta(days=1)), "countBack": days}
    d = _json(get(Request(url, "POST", json.dumps(body).encode(), {"content-type": "application/json"})))
    rows = [r for r in d if r.get("symbol") == symbol] if isinstance(d, list) else []
    if not rows:
        raise SourceError(f"vietcap {symbol}: không có dữ liệu")
    pts = [(_day(t), float(c) * scale) for t, c in zip(rows[0].get("t") or [], rows[0].get("c") or [])]
    return Fetched(_within(pts, start, end), url)


# -- world series (MSN) -------------------------------------------------------------------------

MSN_CONFIG = (
    "https://assets.msn.com/resolver/api/resolve/v3/config/?expType=AppConfig&expInstance=default&apptype=finance"
    "&v=20240101.1&targetScope="
    + urllib.parse.quote(
        json.dumps(
            {
                "audienceMode": "adult",
                "browser": {"browserType": "chrome", "version": "124", "ismobile": "false"},
                "deviceFormFactor": "desktop",
                "domain": "www.msn.com",
                "locale": {
                    "content": {"language": "vi", "market": "vn"},
                    "display": {"language": "vi", "market": "vn"},
                },
                "os": "linux",
                "platform": "web",
                "pageType": "finance",
            },
            separators=(",", ":"),
        )
    )
)
MSN_KEY_PATH = ("shared/msn-ns/HoroscopeAnswerCardWC/default", "properties", "horoscopeAnswerServiceClientSettings")
_msn_key: Dict[str, object] = {}


def msn_key(get: Http = http, fresh: bool = False) -> str:
    """The anonymous key MSN's own pages use, from its public configuration (kept for a day)."""
    if not fresh and _msn_key.get("key") and time.time() - float(_msn_key["at"]) < 86400:
        return str(_msn_key["key"])
    cfg = _json(get(Request(MSN_CONFIG)))
    node = cfg["configs"][MSN_KEY_PATH[0]]
    for k in MSN_KEY_PATH[1:]:
        node = node[k]
    _msn_key.update(key=node["apikey"], at=time.time())
    return str(node["apikey"])


def msn_many(ids: List[str], start: date, end: date, get: Http = http) -> Tuple[Dict[str, List[Point]], str]:
    """Several MSN instruments in one request: {id: points}."""

    def ask(key: str) -> Tuple[object, str]:
        q = urllib.parse.urlencode(
            {
                "apikey": key,
                "StartTime": f"{start.isoformat()}T00:00:00.000Z",
                "EndTime": f"{end.isoformat()}T23:59:59.000Z",
                "timeframe": 1,
                "ocid": "finance-utils-peregrine",
                "cm": "vi-vn",
                "it": "web",
                "scn": "ANON",
                "ids": ",".join(ids),
                "type": "All",
                "wrapodata": "false",
                "disableSymbol": "false",
            }
        )
        url = f"https://assets.msn.com/service/Finance/Charts/TimeRange?{q}"
        return _json(get(Request(url))), url.replace(key, "…")

    try:
        d, url = ask(msn_key(get))
    except Exception:  # noqa: BLE001 — a key that has expired: fetch it again, once
        d, url = ask(msn_key(get, fresh=True))
    out: Dict[str, List[Point]] = {}
    for item in d if isinstance(d, list) else []:
        for x in item if isinstance(item, list) else [item]:
            s = x.get("series") or {}
            pts = [(str(t)[:10], float(p)) for t, p in zip(s.get("timeStamps") or [], s.get("prices") or [])]
            out[x.get("instrumentId")] = _within(pts, start, end)
    return out, url


def msn(symbol: str, start: date, end: date, get: Http = http, scale: float = 1.0) -> Fetched:
    got, url = msn_many([symbol], start, end, get)
    if symbol not in got:
        raise SourceError(f"msn {symbol}: không có dữ liệu")
    return Fetched([(d, v * scale) for d, v in got[symbol]], url)


# -- crypto ------------------------------------------------------------------------------------


def binance(symbol: str, start: date, end: date, get: Http = http, scale: float = 1.0) -> Fetched:
    pts: List[Point] = []
    t0, stop, url = _unix(start) * 1000, _unix(end + timedelta(days=1)) * 1000, ""
    while t0 < stop:
        q = urllib.parse.urlencode(
            {"symbol": symbol, "interval": "1d", "startTime": t0, "endTime": stop - 1, "limit": 1000}
        )
        url = f"https://api.binance.com/api/v3/klines?{q}"
        rows = _json(get(Request(url)))
        if not isinstance(rows, list):
            raise SourceError(f"binance {symbol}: {str(rows)[:80]}")
        if not rows:
            break
        pts += [(_day(r[0] / 1000), float(r[4]) * scale) for r in rows]
        t0 = int(rows[-1][0]) + 86_400_000
        if len(rows) < 1000:
            break
    return Fetched(_within(pts, start, end), url)


# -- Vietnam: USD rate, SJC gold, government yields, foreign flows ----------------------------------


def _days(start: date, end: date, step: int = 1) -> List[date]:
    out, d = [], end
    while d >= start:  # newest first, then sorted: the end day is always asked
        out.append(d)
        d -= timedelta(days=step)
    return sorted(out)


def _by_day(start: date, end: date, step: int, one: Callable[[date], Optional[float]]) -> List[Point]:
    """One request per day asked. A day that fails is skipped (today's page often does not exist yet: PNJ answers
    422 until the day ends); only when every day failed is the last error raised."""
    pts: List[Point] = []
    errors: List[Exception] = []
    days = _days(start, end, step)
    for d in days:
        try:
            v = one(d)
        except Exception as exc:  # noqa: BLE001 — see above
            errors.append(exc)
            continue
        if v is not None:
            pts.append((d.isoformat(), v))
    if errors and len(errors) == len(days):
        raise errors[-1]
    return pts


def vcb(currency: str, start: date, end: date, get: Http = http, scale: float = 1.0, step: int = 1) -> Fetched:
    """Vietcombank's transfer (chuyển khoản) buying rate, one request a day asked."""
    url = "https://www.vietcombank.com.vn/api/exchangerates?date={}"

    def one(d: date) -> Optional[float]:
        rows = (_json(get(Request(url.format(d.isoformat())))) or {}).get("Data") or []
        hit = [r for r in rows if r.get("currencyCode") == currency]
        return _num(hit[0]["transfer"].replace(",", "")) * scale if hit and hit[0].get("transfer") else None

    return Fetched(_by_day(start, end, step, one), url.format(end.isoformat()))


def pnj_sjc(day: date, raw: bytes) -> Optional[float]:
    """The last SJC selling price of the day in Ho Chi Minh City, in VND per lượng (``"146.500"`` → 146,500,000)."""
    d = _json(raw)
    for loc in d.get("locations") or []:
        if loc.get("name") != "TPHCM":
            continue
        for g in loc.get("gold_type") or []:
            if g.get("name") == "SJC" and g.get("data"):
                last = max(g["data"], key=lambda r: datetime.strptime(r["updated_at"], "%d/%m/%Y %H:%M:%S"))
                return float(str(last["gia_ban"]).replace(".", "").replace(",", "")) * 1000
    return None


def pnj(kind: str, start: date, end: date, get: Http = http, scale: float = 1.0, step: int = 1) -> Fetched:
    url = "https://edge-api.pnj.io/ecom-frontend/v1/get-gold-price-history?zone=00&date={:%Y%m%d}"

    def one(d: date) -> Optional[float]:
        v = pnj_sjc(d, get(Request(url.format(d))))
        return None if v is None else v * scale

    return Fetched(_by_day(start, end, step, one), url.format(end))


HNX_URL = "https://www.hnx.vn/ModuleReportBonds/Bond_YieldCurve/SearchAndNextPageYieldCurveData"
TENORS = {"3 tháng": "3M", "6 tháng": "6M", "9 tháng": "9M", "1 năm": "1Y", "2 năm": "2Y", "3 năm": "3Y",
          "5 năm": "5Y", "7 năm": "7Y", "10 năm": "10Y", "15 năm": "15Y", "20 năm": "20Y", "30 năm": "30Y"}  # fmt: skip


def hnx_curve(html: str) -> Dict[str, float]:
    """The HNX curve table: {tenor: annual spot rate in %}. Columns: tenor, continuous spot, par yield, annual
    spot; the annual spot is the last."""
    import html as htmllib

    out = {}
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        cells = [htmllib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c))).strip()
                 for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, re.S)]  # fmt: skip
        if len(cells) >= 4 and cells[0] in TENORS and cells[-1]:
            out[TENORS[cells[0]]] = _num(cells[-1])
    return out


def hnx(tenor: str, start: date, end: date, get: Http = http, scale: float = 1.0, step: int = 1) -> Fetched:
    headers = {
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.hnx.vn/trai-phieu/duong-cong-loi-suat.html",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    def one(d: date) -> Optional[float]:
        body = urllib.parse.urlencode({"pDate": d.strftime("%d/%m/%Y")}).encode()
        curve = hnx_curve(get(Request(HNX_URL, "POST", body, headers, insecure=True)).decode("utf-8", "replace"))
        return curve[tenor] * scale if tenor in curve else None

    return Fetched(_by_day(start, end, step, one), HNX_URL)


WGB_URL = "https://www.worldgovernmentbonds.com/wp-json/common/v1/historical"


def wgb(symbol: str, start: date, end: date, get: Http = http, scale: float = 1.0) -> Fetched:
    """worldgovernmentbonds.com's history of one country's 10-year (``symbol``: its country number, 58 Vietnam)."""
    var = {
        "JS_VARIABLE": "jsGlobalVars",
        "FUNCTION": "Bond",
        "DOMESTIC": True,
        "ENDPOINT": WGB_URL,
        "DATE_RIF": "2099-12-31",
        "OBJ": {"UNIT": "%", "DECIMAL": 3, "UNIT_DELTA": "bp", "DECIMAL_DELTA": 1},
        "COUNTRY1": {"SYMBOL": symbol},
        "COUNTRY2": None,
        "OBJ1": {"DURATA_STRING": "10 Years", "DURATA": 120},
        "OBJ2": None,
    }
    headers = {
        "content-type": "application/json",
        "Origin": "https://www.worldgovernmentbonds.com",
        "Referer": "https://www.worldgovernmentbonds.com/bond-historical-data/vietnam/10-years/",
    }
    d = _json(get(Request(WGB_URL, "POST", json.dumps({"GLOBALVAR": var}).encode(), headers)))
    if not d.get("success"):
        raise SourceError(f"wgb: {str(d)[:80]}")
    q = (d.get("result") or {}).get("quote") or {}
    pts = [(r["DATA_VAL"], float(r["CLOSE_VAL"]) * scale) for r in q.values()]
    return Fetched(_within(pts, start, end), WGB_URL)


def cafef(symbol: str, start: date, end: date, get: Http = http, scale: float = 1.0) -> Fetched:
    """Foreign investors' net buying on HOSE (``GTDGRong``, VND), 30 days a page, asked a year at a time (a longer
    range is silently answered with the last ~238 days). cafef's history is complete from 2022."""
    pts: List[Point] = []
    url = ""
    lo = start
    while lo <= end:
        hi = min(end, lo + timedelta(days=364))
        got = _cafef_window(symbol, lo, hi, get, scale)
        pts += got.points
        url = got.url
        lo = hi + timedelta(days=1)
    return Fetched(_within(pts, start, end), url)


def _cafef_window(symbol: str, start: date, end: date, get: Http, scale: float) -> Fetched:
    pts, url = [], ""
    for page in range(1, 200):
        q = urllib.parse.urlencode(
            {
                "Symbol": symbol,
                "StartDate": start.strftime("%m/%d/%Y"),
                "EndDate": end.strftime("%m/%d/%Y"),
                "PageIndex": page,
                "PageSize": 30,
            }
        )
        url = f"https://cafef.vn/du-lieu/Ajax/PageNew/DataHistory/GDKhoiNgoai.ashx?{q}"
        data = (_json(get(Request(url))) or {}).get("Data") or {}
        rows = data.get("Data") or []
        for r in rows:
            d = datetime.strptime(r["Ngay"], "%d/%m/%Y").date().isoformat()
            pts.append((d, float(r["GTDGRong"]) * scale))
        if not rows or page * 30 >= int(data.get("TotalCount") or 0):
            break
    return Fetched(_within(pts, start, end), url)


ADAPTERS: Dict[str, Callable[..., Fetched]] = {
    "vndirect": vndirect,
    "vietcap": vietcap,
    "msn": msn,
    "binance": binance,
    "vcb": vcb,
    "pnj": pnj,
    "hnx": hnx,
    "wgb": wgb,
    "cafef": cafef,
}
DATED = {"vcb", "pnj", "hnx"}  # one request a day asked: a backfill samples them weekly
