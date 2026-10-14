import argparse
import logging
import sys
import time
from datetime import datetime, time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from . import analytics, db, demo, export, ledger, marketdata

log = logging.getLogger("tracker")
NY = ZoneInfo("America/New_York")


def market_is_open(now: datetime | None = None) -> bool:
    """Regular NYSE session, with five minutes after the bell to catch the
    closing print. Exchange holidays aren't modelled; on those days a refresh
    just re-reads the previous session, which is harmless."""
    now = (now or datetime.now(NY)).astimezone(NY)
    return now.weekday() < 5 and dtime(9, 30) <= now.time() <= dtime(16, 5)


def cmd_init(conn, args):
    db.migrate(conn)
    n = db.load_universe(conn, Path(args.universe))
    print(f"schema ready, {n} equities in the universe (+ {db.BENCHMARK[0]} benchmark)")


def cmd_backfill(conn, args):
    marketdata.sync_daily(conn, db.active_tickers(conn), history_days=args.days)


def refresh(conn, quotes: bool = True):
    tickers = db.active_tickers(conn)
    marketdata.sync_daily(conn, tickers)
    if quotes:
        marketdata.refresh_quotes(conn, tickers)
    analytics.refresh_analytics(conn)
    export.export_all(conn)


def cmd_refresh(conn, args):
    if args.market_hours_only and not market_is_open():
        log.info("market closed, nothing to do")
        return
    refresh(conn)
    cmd_status(conn, args)


def cmd_watch(conn, args):
    log.info("refreshing every %ds during market hours (ctrl+c to stop)", args.every)
    was_open = False
    while True:
        is_open = market_is_open()
        # One extra pass right after the close so the dashboard ends the day on the closing prints.
        if is_open or was_open:
            try:
                refresh(conn)
            except Exception:
                log.exception("refresh failed, will retry next cycle")
        was_open = is_open
        time.sleep(args.every)


def cmd_seed_demo(conn, args):
    counts = demo.seed(conn, reset=args.reset)
    for name, n in counts.items():
        print(f"  {name:<16} {n} names")
    analytics.refresh_analytics(conn)
    export.export_all(conn)


def cmd_trade(conn, args):
    ledger.record_trade(conn, args.portfolio, args.ticker, args.side, args.qty, args.price,
                        args.date, args.fees)
    analytics.refresh_analytics(conn)
    print(f"recorded {args.side.upper()} {args.qty:g} {args.ticker.upper()} @ {args.price}")


def cmd_import(conn, args):
    n = ledger.import_trades(conn, Path(args.csv))
    analytics.refresh_analytics(conn)
    print(f"imported {n} trades")


def cmd_export(conn, args):
    out = export.export_all(conn, Path(args.out) if args.out else export.DEFAULT_DIR)
    print(f"wrote {len(out)} files to {out[0].parent}")


def cmd_status(conn, args):
    live = pd.read_sql_query(
        """
        SELECT l.portfolio, l.open_positions AS names, l.market_value, l.unrealized_pnl,
               l.unrealized_pct, l.day_pnl, l.day_pct, r.total_return AS twr, r.sharpe,
               r.max_drawdown AS max_dd, r.beta, l.stale_prices AS stale
        FROM v_portfolio_live l LEFT JOIN risk_summary r USING (portfolio_id)
        ORDER BY l.market_value DESC
        """, conn)
    if live.empty:
        print("no positions yet")
        return

    money = lambda x: f"{x:,.0f}"
    pct = lambda x: "" if pd.isna(x) else f"{x:+.2%}"
    num = lambda x: "" if pd.isna(x) else f"{x:.2f}"
    fmt = {"market_value": money, "unrealized_pnl": money, "day_pnl": money,
           "unrealized_pct": pct, "day_pct": pct, "twr": pct, "max_dd": pct,
           "sharpe": num, "beta": num}
    print()
    print(live.to_string(index=False, formatters=fmt))

    w = conn.execute(
        """SELECT COUNT(*), SUM(day_change_pct > 0), SUM(day_change_pct < 0),
                  SUM(price_source = 'intraday'), MAX(price_time)
           FROM v_watchlist"""
    ).fetchone()
    held = conn.execute("SELECT COUNT(DISTINCT ticker) FROM position WHERE qty > 0").fetchone()[0]
    print(f"\nuniverse {w[0]} names ({held} held) | up {w[1]} / down {w[2]} | "
          f"{w[3]} live quotes, latest {w[4]}")

    # A ticker that stops getting bars has usually been delisted, merged or renamed
    # (BK became BNY, for example). Yahoo just returns nothing, so flag it here.
    gone = [r[0] for r in conn.execute(
        """
        SELECT s.ticker FROM security s LEFT JOIN daily_bar b ON b.ticker = s.ticker
        WHERE s.is_active = 1 GROUP BY s.ticker
        HAVING COALESCE(MAX(b.bar_date), '') < date((SELECT MAX(bar_date) FROM daily_bar), '-7 days')
        """)]
    if gone:
        print(f"no recent prices for {', '.join(gone)} - check data/universe.csv")


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m tracker")
    p.add_argument("--db", help="SQLite file (default: portfolio.db in the repo root, or $TRACKER_DB)")
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="create tables/views and load the ticker universe")
    s.add_argument("--universe", default=str(db.UNIVERSE_CSV))
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("backfill", help="download daily history for every active ticker")
    s.add_argument("--days", type=int, default=400)
    s.set_defaults(fn=cmd_backfill)

    s = sub.add_parser("refresh", help="pull latest prices, recompute analytics, export for Power BI")
    s.add_argument("--market-hours-only", action="store_true",
                   help="exit immediately outside NYSE hours (for schedulers)")
    s.set_defaults(fn=cmd_refresh)

    s = sub.add_parser("watch", help="refresh on a loop while the market is open")
    s.add_argument("--every", type=int, default=300, help="seconds between refreshes")
    s.set_defaults(fn=cmd_watch)

    s = sub.add_parser("seed-demo", help="create sample portfolios from the backfilled history")
    s.add_argument("--reset", action="store_true", help="wipe existing trades first")
    s.set_defaults(fn=cmd_seed_demo)

    s = sub.add_parser("trade", help="record a single trade")
    s.add_argument("portfolio")
    s.add_argument("side", choices=["buy", "sell", "BUY", "SELL"])
    s.add_argument("ticker")
    s.add_argument("qty", type=float)
    s.add_argument("price", type=float)
    s.add_argument("--date", help="YYYY-MM-DD, default today")
    s.add_argument("--fees", type=float, default=0.0)
    s.set_defaults(fn=cmd_trade)

    s = sub.add_parser("import", help="load trades from a CSV (portfolio,ticker,trade_date,side,qty,price[,fees])")
    s.add_argument("csv")
    s.set_defaults(fn=cmd_import)

    s = sub.add_parser("export", help="write the Power BI CSVs without fetching prices")
    s.add_argument("--out")
    s.set_defaults(fn=cmd_export)

    s = sub.add_parser("status", help="print portfolio summary")
    s.set_defaults(fn=cmd_status)

    args = p.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
                        datefmt="%H:%M:%S")
    logging.getLogger("yfinance").setLevel(logging.WARNING)

    conn = db.connect(args.db)
    if args.cmd != "init":
        db.migrate(conn)   # cheap, and keeps views current after a pull
    try:
        args.fn(conn, args)
    except (ledger.LedgerError, demo.DemoError) as e:
        sys.exit(f"error: {e}")
    except KeyboardInterrupt:
        pass
    finally:
        conn.close()


if __name__ == "__main__":
    main()
