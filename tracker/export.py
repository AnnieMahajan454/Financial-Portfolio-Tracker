"""Flat files for the Power BI model.

Power BI Desktop has no built-in SQLite connector, so rather than make every
machine install an ODBC driver, each refresh writes the model tables as CSV.
Files are written to a temp name and swapped in, so a Power BI refresh that
lands mid-export reads the previous complete file instead of half a file.
"""
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .db import ROOT

DEFAULT_DIR = ROOT / "exports" / "powerbi"

TABLES = {
    "dim_security":     "SELECT ticker, name, sector, kind, is_active FROM security",
    "dim_portfolio":    "SELECT portfolio_id, name AS portfolio, strategy FROM portfolio",
    "fact_position":    "SELECT * FROM v_position_live",
    "fact_watchlist":   "SELECT * FROM v_watchlist",
    "fact_perf_daily":  "SELECT * FROM perf_daily",
    "fact_trade":       """SELECT trade_id, portfolio_id, ticker, trade_date, side, qty, price, fees,
                                  qty * price AS gross_amount
                           FROM trade""",
    "risk_summary":     "SELECT * FROM risk_summary",
    "fetch_log":        "SELECT * FROM fetch_run ORDER BY run_id DESC LIMIT 200",
}


def export_all(conn: sqlite3.Connection, out_dir: Path = DEFAULT_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, sql in TABLES.items():
        df = pd.read_sql_query(sql, conn).round(6)
        target = out_dir / f"{name}.csv"
        tmp = target.with_suffix(".csv.tmp")
        df.to_csv(tmp, index=False, encoding="utf-8")
        os.replace(tmp, target)
        written.append(target)

    stamp = out_dir / "refresh_info.csv"
    last = conn.execute(
        "SELECT MAX(finished_at) FROM fetch_run WHERE kind = 'intraday' AND finished_at IS NOT NULL"
    ).fetchone()[0]
    pd.DataFrame([{
        "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "last_quote_pull": last,
    }]).to_csv(stamp, index=False)
    written.append(stamp)
    return written
