"""Trade ledger -> positions, using average cost.

Positions are always rebuilt by replaying the trade table rather than being
patched incrementally. It's a few hundred rows, replay is instant, and it means
a corrected or back-dated trade can't leave the position table out of sync.
"""
import csv
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .db import ensure_portfolio

EPS = 1e-9


class LedgerError(ValueError):
    pass


@dataclass
class Position:
    qty: float = 0.0
    avg_cost: float = 0.0
    realized_pnl: float = 0.0
    opened_on: str | None = None

    def apply(self, side: str, qty: float, price: float, fees: float, on: str) -> None:
        if side == "BUY":
            total_cost = self.qty * self.avg_cost + qty * price + fees
            self.qty += qty
            self.avg_cost = total_cost / self.qty
            if self.opened_on is None:
                self.opened_on = on
        elif side == "SELL":
            if qty > self.qty + EPS:
                raise LedgerError(f"sell of {qty:g} on {on} exceeds held quantity {self.qty:g}")
            self.realized_pnl += qty * (price - self.avg_cost) - fees
            self.qty -= qty
            if self.qty <= EPS:
                # Flat. Keep realized P&L, reset the basis for any re-entry.
                self.qty, self.avg_cost, self.opened_on = 0.0, 0.0, None
        else:
            raise LedgerError(f"unknown side {side!r}")


def replay(trades) -> dict[tuple[int, str], Position]:
    """trades: iterable of rows with portfolio_id, ticker, side, qty, price, fees, trade_date,
    already in execution order."""
    book: dict[tuple[int, str], Position] = {}
    for t in trades:
        key = (t["portfolio_id"], t["ticker"])
        pos = book.setdefault(key, Position())
        try:
            pos.apply(t["side"], t["qty"], t["price"], t["fees"], t["trade_date"])
        except LedgerError as e:
            raise LedgerError(f"{t['ticker']} in portfolio {t['portfolio_id']}: {e}") from None
    return book


def rebuild_positions(conn: sqlite3.Connection) -> int:
    trades = conn.execute(
        "SELECT portfolio_id, ticker, side, qty, price, fees, trade_date "
        "FROM trade ORDER BY trade_date, trade_id"
    ).fetchall()
    book = replay(trades)
    conn.execute("DELETE FROM position")
    conn.executemany(
        "INSERT INTO position (portfolio_id, ticker, qty, avg_cost, realized_pnl, opened_on) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [(pid, tkr, p.qty, p.avg_cost, p.realized_pnl, p.opened_on or "")
         for (pid, tkr), p in book.items()],
    )
    return sum(1 for p in book.values() if p.qty > 0)


def record_trade(conn: sqlite3.Connection, portfolio: str, ticker: str, side: str,
                 qty: float, price: float, trade_date: str | None = None,
                 fees: float = 0.0) -> None:
    ticker, side = ticker.upper(), side.upper()
    trade_date = trade_date or date.today().isoformat()
    if not conn.execute("SELECT 1 FROM security WHERE ticker = ?", (ticker,)).fetchone():
        raise LedgerError(f"{ticker} is not in the security master; add it to data/universe.csv")

    # One transaction: if the replay rejects the trade (e.g. overselling), nothing is written.
    with conn:
        pid = ensure_portfolio(conn, portfolio)
        conn.execute(
            "INSERT INTO trade (portfolio_id, ticker, trade_date, side, qty, price, fees) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (pid, ticker, trade_date, side, qty, price, fees),
        )
        rebuild_positions(conn)


def import_trades(conn: sqlite3.Connection, csv_path: Path) -> int:
    """CSV columns: portfolio,ticker,trade_date,side,qty,price[,fees]"""
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    with conn:
        for r in rows:
            pid = ensure_portfolio(conn, r["portfolio"].strip())
            conn.execute(
                "INSERT INTO trade (portfolio_id, ticker, trade_date, side, qty, price, fees) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (pid, r["ticker"].strip().upper(), r["trade_date"].strip(),
                 r["side"].strip().upper(), float(r["qty"]), float(r["price"]),
                 float(r.get("fees") or 0)),
            )
        rebuild_positions(conn)
    return len(rows)
