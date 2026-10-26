"""Fetch one outlet's headlines 2024-01 → 2026-06 into the replay's feed cache (same file names), backing off on errors."""
import sys, time
from datetime import date, timedelta
sys.path.insert(0, "scripts")
import replay
site = sys.argv[1]
replay.SITES = {site: replay.SITES[site]}
d = date(2024, 1, 1)
while d < date(2026, 7, 1):
    end = (d.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    for attempt in range(6):
        try:
            print(d, "items", replay.fetch(d, end), flush=True)
            break
        except Exception as e:
            print(d, "error", repr(e)[:120], "sleep", 60 * 2 ** attempt, flush=True)
            time.sleep(60 * 2 ** attempt)
    d = end + timedelta(days=1)
print("done", flush=True)
