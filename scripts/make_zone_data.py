"""The AI zone's data folder (ZONE-01): the shipped catalogues only — the market's instruments, the factors and
model, the news configuration. No client, no staff, no sample statement is copied, so the zone could not read one
even by mistake. Usage: python scripts/make_zone_data.py [data/zone]"""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ("market.json", "factors.json", "factor_model.json", "news_config.json")


def main(out: str = "data/zone") -> None:
    dest = (ROOT / out).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        shutil.copy2(ROOT / "data" / name, dest / name)
    print(f"{dest}: {', '.join(FILES)}")


if __name__ == "__main__":
    main(*sys.argv[1:2])
