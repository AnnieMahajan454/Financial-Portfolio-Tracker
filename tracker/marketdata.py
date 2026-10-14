"""Price collection from Yahoo Finance via yfinance.

Two feeds:
  * daily bars  -> daily_bar   (history for performance, 52w range, prev close)
  * 1-min bars  -> quote       (last print of the current session)

Requests go out in batches through yf.download, which is far faster than
hitting Ticker.info once per symbol and much less likely to get rate limited.
Tickers that come back empty are retried once on their own before being
logged as missing in fetch_run.
"""
import logging
import sqlite3
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)

BATCH_SIZE = 80
DAILY_OVERLAP_DAYS = 7   # re-pull the last week so late corrections from Yahoo land


def _batches(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def to_long(raw: pd.DataFrame) -> pd.DataFrame:
    """yf.download gives wide (field, ticker) columns; turn that into one row per
    ticker per timestamp with lower-case column names."""
    if raw is None or raw.empty:
        return pd.DataFrame()
    long = raw.stack(level="Ticker", future_stack=True)
    long = long.dropna(subset=["Close"])
    long.index = long.index.set_names(["ts", "ticker"])
    long = long.reset_index()
    long.columns = [str(c).lower().replace(" ", "_") for c in long.columns]
    return long


def _download(tickers: list[str], **kwargs) -> pd.DataFrame:
    frames = []
    for batch in _batches(tickers, BATCH_SIZE):
        raw = yf.download(batch, auto_adjust=False, progress=False, threads=True,
                          group_by="column", multi_level_index=True, **kwargs)
        frames.append(to_long(raw))

    got = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    have = set(got["ticker"]) if not got.empty else set()
    missing = [t for t in tickers if t not in have]
    if missing:
        # Yahoo drops a few symbols per batch now and then; a second, unthreaded
        # pass usually picks them up.
        log.info("retrying %d tickers: %s", len(missing), " ".join(missing[:20]))
        raw = yf.download(missing, auto_adjust=False, progress=False, threads=False,
                          group_by="column", multi_level_index=True, **kwargs)
        got = pd.concat([got, to_long(raw)], ignore_index=True)
    return got


def _start_run(conn, kind, n):
    cur = conn.execute(
        "INSERT INTO fetch_run (kind, started_at, requested) VALUES (?, ?, ?)",
        (kind, _utcnow(), n),
    )
    conn.commit()
    return cur.lastrowid


def _finish_run(conn, run_id, received: set, requested: list):
    missing = sorted(set(requested) - received)
    conn.execute(
        "UPDATE fetch_run SET finished_at = ?, received = ?, missing = ? WHERE run_id = ?",
        (_utcnow(), len(received), " ".join(missing) or None, run_id),
    )
    conn.commit()
    if missing:
        log.warning("no data for %d tickers: %s", len(missing), " ".join(missing))


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _none_if_nan(x):
    return None if pd.isna(x) else x


def sync_daily(conn: sqlite3.Connection, tickers: list[str], history_days: int = 400) -> int:
    """Bring daily_bar up to date. New tickers get `history_days` of history,
    existing ones are topped up from their last bar."""
    last = dict(conn.execute("SELECT ticker, MAX(bar_date) FROM daily_bar GROUP BY ticker"))
    fresh = [t for t in tickers if t not in last]
    known = [t for t in tickers if t in last]

    jobs = []
    if fresh:
        jobs.append((fresh, date.today() - timedelta(days=history_days)))
    if known:
        oldest = min(date.fromisoformat(last[t]) for t in known)
        jobs.append((known, oldest - timedelta(days=DAILY_OVERLAP_DAYS)))

    run_id = _start_run(conn, "daily", len(tickers))
    received, written = set(), 0
    for group, start in jobs:
        df = _download(group, start=start.isoformat(), interval="1d")
        if df.empty:
            continue
        df["bar_date"] = pd.to_datetime(df["ts"]).dt.strftime("%Y-%m-%d")
        rows = [
            (r.ticker, r.bar_date, _none_if_nan(r.open), _none_if_nan(r.high),
             _none_if_nan(r.low), float(r.close), _none_if_nan(r.adj_close),
             None if pd.isna(r.volume) else int(r.volume))
            for r in df.itertuples(index=False)
        ]
        with conn:
            conn.executemany(
                """
                INSERT INTO daily_bar (ticker, bar_date, open, high, low, close, adj_close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (ticker, bar_date) DO UPDATE SET
                    open = excluded.open, high = excluded.high, low = excluded.low,
                    close = excluded.close, adj_close = excluded.adj_close,
                    volume = excluded.volume
                """,
                rows,
            )
        received |= set(df["ticker"])
        written += len(rows)

    _finish_run(conn, run_id, received, tickers)
    log.info("daily bars: %d rows for %d tickers", written, len(received))
    return written


def latest_prints(df: pd.DataFrame) -> pd.DataFrame:
    """Reduce 1-minute bars to the last print per ticker plus that session's volume."""
    if df.empty:
        return df
    df = df.copy()
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df["session"] = df["ts"].dt.tz_convert("America/New_York").dt.date
    last_session = df.groupby("ticker")["session"].transform("max")
    df = df[df["session"] == last_session].sort_values("ts")
    return df.groupby("ticker").agg(
        price=("close", "last"),
        quote_time=("ts", "last"),
        session=("session", "last"),
        day_volume=("volume", "sum"),
    ).reset_index()


def refresh_quotes(conn: sqlite3.Connection, tickers: list[str]) -> int:
    """Pull 1-minute bars for the current session and store the last print.

    prev_close is read from daily_bar (the close of the session before the
    quote's session), so sync_daily should run first.
    """
    run_id = _start_run(conn, "intraday", len(tickers))
    prints = latest_prints(_download(tickers, period="1d", interval="1m", prepost=False))
    fetched_at = _utcnow()

    rows = [
        (r.ticker, float(r.price), r.ticker, r.session.isoformat(),
         int(r.day_volume) if not pd.isna(r.day_volume) else None,
         r.quote_time.isoformat(), fetched_at)
        for r in prints.itertuples(index=False)
    ]
    with conn:
        conn.executemany(
            """
            INSERT INTO quote (ticker, price, prev_close, day_volume, quote_time, fetched_at)
            VALUES (?, ?,
                    (SELECT close FROM daily_bar
                      WHERE ticker = ? AND bar_date < ? ORDER BY bar_date DESC LIMIT 1),
                    ?, ?, ?)
            ON CONFLICT (ticker) DO UPDATE SET
                price = excluded.price, prev_close = excluded.prev_close,
                day_volume = excluded.day_volume, quote_time = excluded.quote_time,
                fetched_at = excluded.fetched_at
            """,
            rows,
        )

    _finish_run(conn, run_id, set(prints["ticker"]) if not prints.empty else set(), tickers)
    log.info("quotes: %d of %d tickers", len(rows), len(tickers))
    return len(rows)
