"""The SQLite state exported to PostgreSQL and checked (BRD-RULE-DATA-10, src/control/pgexport.py, ADR-0025).

    python scripts/export_postgres.py --schema                 # the PostgreSQL DDL only
    python scripts/export_postgres.py --out export.sql         # the load file (schema + COPY), for psql -f
    python scripts/export_postgres.py --docker mrf-g4-pg --start postgres:16-alpine --stop
        # a throwaway PostgreSQL in Docker (reached by docker exec only; no port is opened), the export loaded into
        # a fresh database, then checked: rows and sums by SQL, and every row read back, rebuilt and compared

Works on the database ``MF_STATE`` names (default data/state.db), read only. A sealed database needs the keys
(``MF_DATA_KEYS``) to split its JSON; sealed values that are not split are copied as they are and still open.
``--report FILE`` writes the check as JSON. Exit status 1 when the check fails.
"""

import argparse
import json
import secrets as pysecrets
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from control import pgexport  # noqa: E402
from wealth.paths import state_path  # noqa: E402

DB = "mrf"


class Psql:
    """psql in a container, by ``docker exec``: no port, no driver."""

    def __init__(self, container: str):
        self.container = container

    def run(self, *args: str, stdin: bytes = None, db: str = DB) -> str:
        cmd = ["docker", "exec", "-i", self.container, "psql", "-U", "postgres", "-d", db, "-X", "-q", *args]
        p = subprocess.run(cmd, input=stdin, capture_output=True)
        if p.returncode:
            raise SystemExit(f"psql: {p.stderr.decode(errors='replace').strip()}")
        return p.stdout.decode("utf-8")

    def read(self, sql: str):
        out = self.run("-At", "-c", f"select row_to_json(x) from ({sql}) x")
        return [json.loads(line) for line in out.splitlines() if line]

    def fresh(self) -> None:
        self.run("-c", f"drop database if exists {DB}", db="postgres")
        self.run("-c", f"create database {DB}", db="postgres")


def _docker(*args: str) -> bool:
    return subprocess.run(["docker", *args], capture_output=True).returncode == 0


def start(container: str, image: str) -> None:
    up = subprocess.run(["docker", "ps", "-q", "-f", f"name=^{container}$"], capture_output=True, text=True)
    password = f"POSTGRES_PASSWORD={pysecrets.token_urlsafe(18)}"
    if not up.stdout.strip() and not _docker("run", "-d", "--rm", "--name", container, "-e", password, image):
        raise SystemExit(f"{container}: docker run {image} failed")
    for _ in range(60):
        # the image's first start restarts the server once after its init scripts: wait for a real query
        if _docker("exec", container, "psql", "-U", "postgres", "-c", "select 1"):
            return
        time.sleep(1)
    raise SystemExit(f"{container}: PostgreSQL did not come up")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", default=None, help="the SQLite file (default: MF_STATE or data/state.db)")
    ap.add_argument("--schema", action="store_true", help="print the PostgreSQL DDL and stop")
    ap.add_argument("--out", help="write the load file here")
    ap.add_argument("--docker", metavar="CONTAINER", help="load into this PostgreSQL container and check")
    ap.add_argument("--start", metavar="IMAGE", help="start the container from this image when it is not running")
    ap.add_argument("--stop", action="store_true", help="remove the container afterwards")
    ap.add_argument("--report", help="write the check as JSON here")
    a = ap.parse_args()

    path = Path(a.db) if a.db else state_path()
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    if a.schema:
        print(";\n\n".join(pgexport.ddl(con)) + ";")
        return
    t0 = time.time()
    body = "".join(pgexport.script(con)).encode("utf-8")
    print(f"load file: {len(body) / 1e6:.1f} MB in {time.time() - t0:.1f} s")
    if a.out:
        Path(a.out).write_bytes(body)
        print(f"written: {a.out}")
    if not a.docker:
        return
    try:
        if a.start:
            start(a.docker, a.start)
        psql = Psql(a.docker)
        version = psql.run("-At", "-c", "show server_version", db="postgres").strip()
        psql.fresh()
        t0 = time.time()
        psql.run("-f", "-", stdin=body)
        loaded = time.time() - t0
        t0 = time.time()
        report = pgexport.compare(con, psql.read)
        report |= {"postgres": version, "load_s": round(loaded, 2), "check_s": round(time.time() - t0, 2)}
    finally:
        if a.stop:
            subprocess.run(["docker", "rm", "-f", a.docker], capture_output=True)
    print(f"PostgreSQL {version}: loaded in {report['load_s']} s, checked in {report['check_s']} s")
    print(f"{'table':28} {'sqlite':>7} {'postgres':>8}  sums  rows  children")
    for name, e in report["tables"].items():
        kids = ", ".join(f"{k} {v['postgres']}/{v['expected']}" for k, v in e["children"].items())
        same = "ok" if not e["mismatched"] and not e["missing"] else f"{len(e['mismatched'])}≠ {e['missing']} lost"
        print(f"{name:28} {e['sqlite']:>7} {e['postgres']:>8}  {'ok' if e['sums'] else 'NO':4}  {same:4}  {kids}")
    print("CHECK", "PASSED" if report["ok"] else "FAILED")
    if a.report:
        Path(a.report).write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    sys.exit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
