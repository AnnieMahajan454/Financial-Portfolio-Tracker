import csv
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
DEFAULT_DB = ROOT / "portfolio.db"
UNIVERSE_CSV = ROOT / "data" / "universe.csv"

# S&P 500 ETF, used for beta and as the comparison line on the performance page.
BENCHMARK = ("SPY", "SPDR S&P 500 ETF", "Benchmark")


def connect(path: str | os.PathLike | None = None) -> sqlite3.Connection:
    path = path or os.environ.get("TRACKER_DB") or DEFAULT_DB
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # WAL lets Power BI (via ODBC) read while a refresh is writing.
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    for script in sorted(SQL_DIR.glob("*.sql")):
        conn.executescript(script.read_text(encoding="utf-8"))


def load_universe(conn: sqlite3.Connection, csv_path: Path = UNIVERSE_CSV) -> int:
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = [(r["ticker"].strip().upper(), r["name"].strip(), r["sector"].strip())
                for r in csv.DictReader(f)]

    with conn:
        conn.executemany(
            """
            INSERT INTO security (ticker, name, sector) VALUES (?, ?, ?)
            ON CONFLICT (ticker) DO UPDATE
               SET name = excluded.name, sector = excluded.sector, is_active = 1
            """,
            rows,
        )
        conn.execute(
            """
            INSERT INTO security (ticker, name, sector, kind) VALUES (?, ?, ?, 'benchmark')
            ON CONFLICT (ticker) DO NOTHING
            """,
            BENCHMARK,
        )
        # Tickers removed from the file are deactivated, not deleted, because
        # old trades may still point at them.
        placeholders = ",".join("?" * len(rows))
        conn.execute(
            f"UPDATE security SET is_active = 0 "
            f"WHERE kind = 'equity' AND ticker NOT IN ({placeholders})",
            [r[0] for r in rows],
        )
    return len(rows)


def active_tickers(conn: sqlite3.Connection, include_benchmark: bool = True) -> list[str]:
    sql = "SELECT ticker FROM security WHERE is_active = 1"
    if not include_benchmark:
        sql += " AND kind = 'equity'"
    return [r[0] for r in conn.execute(sql + " ORDER BY ticker")]


def ensure_portfolio(conn: sqlite3.Connection, name: str, strategy: str | None = None) -> int:
    row = conn.execute("SELECT portfolio_id FROM portfolio WHERE name = ?", (name,)).fetchone()
    if row:
        return row[0]
    cur = conn.execute("INSERT INTO portfolio (name, strategy) VALUES (?, ?)", (name, strategy))
    return cur.lastrowid
