"""Seed a sample book so the dashboard has something to show.

Three portfolios built from the universe, with trades priced at the actual
historical close on the trade date (so the P&L is real market movement, not
made-up numbers). Between them they hold every ticker in the universe that has
price history. Seeded RNG, so the same database gives the same book.
"""
import random
import sqlite3

from .db import BENCHMARK, ensure_portfolio
from .ledger import rebuild_positions

SEED = 20241016

GROWTH_SECTORS = {"Information Technology", "Communication Services", "Consumer Discretionary"}
INCOME_SECTORS = {"Utilities", "Consumer Staples", "Energy", "Real Estate", "Health Care", "Financials"}


class DemoError(RuntimeError):
    pass


def _fees(notional: float) -> float:
    return round(max(1.0, notional * 0.0005), 2)


def seed(conn: sqlite3.Connection, reset: bool = False) -> dict[str, int]:
    if conn.execute("SELECT COUNT(*) FROM trade").fetchone()[0]:
        if not reset:
            raise DemoError("trade table is not empty; pass --reset to wipe it and reseed")
        with conn:
            for table in ("perf_daily", "risk_summary", "position", "trade", "portfolio"):
                conn.execute(f"DELETE FROM {table}")

    days = [r[0] for r in conn.execute(
        "SELECT bar_date FROM daily_bar WHERE ticker = ? ORDER BY bar_date", (BENCHMARK[0],))]
    if len(days) < 200:
        raise DemoError("need ~1 year of daily bars first; run `python -m tracker backfill`")
    days = days[-252:]

    closes = {(t, d): c for t, d, c in conn.execute(
        "SELECT ticker, bar_date, close FROM daily_bar WHERE bar_date >= ?", (days[0],))}
    universe = [(t, s) for t, s in conn.execute(
        "SELECT ticker, sector FROM security WHERE kind = 'equity' AND is_active = 1 ORDER BY ticker")
        if (t, days[0]) in closes]

    rng = random.Random(SEED)
    growth_pool = [t for t, s in universe if s in GROWTH_SECTORS]
    income_pool = [t for t, s in universe if s in INCOME_SECTORS]
    growth = rng.sample(growth_pool, min(45, len(growth_pool)))
    income = rng.sample(income_pool, min(55, len(income_pool)))
    rest = [t for t, _ in universe if t not in set(growth) | set(income)]
    overlap = rng.sample([t for t, _ in universe if t not in rest], 30)
    core = sorted(rest + overlap)

    books = [
        ("Core Equity", "Broad US large-cap, roughly sector neutral", core, 2_500_000, 20),
        ("Growth", "Tech, communication services and consumer discretionary", growth, 1_100_000, 120),
        ("Dividend Income", "Utilities, staples, energy, REITs, pharma and banks", income, 900_000, 120),
    ]

    trades = []
    for name, strategy, tickers, capital, build_days in books:
        pid = ensure_portfolio(conn, name, strategy)
        weights = [rng.uniform(0.5, 1.5) for _ in tickers]
        total_w = sum(weights)
        for ticker, w in zip(tickers, weights):
            trades += _ticker_trades(rng, pid, ticker, capital * w / total_w, days, closes, build_days)

    trades.sort(key=lambda t: t[2])
    with conn:
        conn.executemany(
            "INSERT INTO trade (portfolio_id, ticker, trade_date, side, qty, price, fees) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            trades,
        )
        rebuild_positions(conn)

    return {name: len(tickers) for name, _, tickers, _, _ in books}


def _ticker_trades(rng, pid, ticker, target, days, closes, build_days):
    def px(i):
        # Walk forward if the stock didn't trade that day.
        for j in range(i, len(days)):
            if (ticker, days[j]) in closes:
                return j, closes[(ticker, days[j])]
        return None, None

    i0, p0 = px(0 if rng.random() < 0.6 else rng.randrange(build_days))
    if i0 is None:
        return []
    qty = max(1, round(target / p0))
    out = [(pid, ticker, days[i0], "BUY", qty, p0, _fees(qty * p0))]
    held = qty

    # Some positions get topped up, some trimmed, a few closed out entirely.
    last = len(days) - 1
    if rng.random() < 0.25 and i0 + 30 < last:
        i1, p1 = px(rng.randrange(i0 + 20, last))
        if i1 is not None:
            add = max(1, round(qty * rng.uniform(0.3, 0.6)))
            out.append((pid, ticker, days[i1], "BUY", add, p1, _fees(add * p1)))
    out.sort(key=lambda t: t[2])

    roll = rng.random()
    if roll < 0.23 and i0 + 40 < last:
        i2, p2 = px(rng.randrange(i0 + 30, last))
        if i2 is not None:
            held = sum(t[4] for t in out if t[2] <= days[i2])
            sell = held if roll < 0.05 else max(1, round(held * rng.uniform(0.25, 0.6)))
            out.append((pid, ticker, days[i2], "SELL", sell, p2, _fees(sell * p2)))

    return out
