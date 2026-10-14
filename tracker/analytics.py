"""Performance and risk numbers that are easier in pandas than in SQL.

v_portfolio_daily gives flow-adjusted daily returns; here they get chained into
a time-weighted index, compared against SPY, and summarised.
"""
import sqlite3
from datetime import date

import numpy as np
import pandas as pd

from .db import BENCHMARK

TRADING_DAYS = 252
RISK_FREE = 0.04   # annual, roughly 3m T-bill; only used for Sharpe


def portfolio_perf(daily: pd.DataFrame, bench_close: pd.Series) -> pd.DataFrame:
    """daily: bar_date, market_value, net_flow, daily_return for one portfolio."""
    df = daily.sort_values("bar_date").reset_index(drop=True)
    r = df["daily_return"].fillna(0.0)
    df["twr_index"] = (1 + r).cumprod()
    df["drawdown"] = df["twr_index"] / df["twr_index"].cummax() - 1

    b = bench_close.reindex(df["bar_date"]).ffill()
    df["bench_index"] = (b / b.dropna().iloc[0]).to_numpy() if b.notna().any() else np.nan
    return df


def risk_stats(perf: pd.DataFrame, bench_close: pd.Series) -> dict:
    r = perf["daily_return"].dropna()
    if len(r) < 2:
        return {"days": len(r)}

    vol = r.std(ddof=1) * np.sqrt(TRADING_DAYS)
    ann_ret = (1 + r).prod() ** (TRADING_DAYS / len(r)) - 1

    bench_r = bench_close.pct_change().reindex(perf.loc[r.index, "bar_date"]).to_numpy()
    mask = ~np.isnan(bench_r)
    beta = None
    if mask.sum() > 20:
        cov = np.cov(r.to_numpy()[mask], bench_r[mask], ddof=1)
        beta = cov[0, 1] / cov[1, 1]

    return {
        "days": len(r),
        "total_return": perf["twr_index"].iloc[-1] - 1,
        "ann_volatility": vol,
        "sharpe": (ann_ret - RISK_FREE) / vol if vol else None,
        "max_drawdown": perf["drawdown"].min(),
        "beta": beta,
    }


def refresh_analytics(conn: sqlite3.Connection) -> None:
    daily = pd.read_sql_query("SELECT * FROM v_portfolio_daily", conn)
    bench = pd.read_sql_query(
        "SELECT bar_date, close FROM daily_bar WHERE ticker = ? ORDER BY bar_date",
        conn, params=(BENCHMARK[0],),
    ).set_index("bar_date")["close"]
    top5 = dict(conn.execute(
        """
        SELECT portfolio_id, SUM(weight) FROM (
            SELECT portfolio_id, weight,
                   ROW_NUMBER() OVER (PARTITION BY portfolio_id ORDER BY weight DESC) AS rn
            FROM v_position_live WHERE is_open
        ) WHERE rn <= 5 GROUP BY portfolio_id
        """
    ))

    perf_rows, risk_rows = [], []
    for pid, grp in daily.groupby("portfolio_id"):
        pid = int(pid)
        perf = portfolio_perf(grp, bench)
        stats = risk_stats(perf, bench)
        perf_rows += [
            (pid, p.bar_date, p.market_value, p.net_flow,
             None if pd.isna(p.daily_return) else p.daily_return,
             p.twr_index, p.drawdown,
             None if pd.isna(p.bench_index) else p.bench_index)
            for p in perf.itertuples(index=False)
        ]
        risk_rows.append((
            pid, date.today().isoformat(), stats["days"], stats.get("total_return"),
            stats.get("ann_volatility"), stats.get("sharpe"), stats.get("max_drawdown"),
            stats.get("beta"), top5.get(pid),
        ))

    with conn:
        conn.execute("DELETE FROM perf_daily")
        conn.executemany("INSERT INTO perf_daily VALUES (?, ?, ?, ?, ?, ?, ?, ?)", perf_rows)
        conn.execute("DELETE FROM risk_summary")
        conn.executemany("INSERT INTO risk_summary VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", risk_rows)
