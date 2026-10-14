import pandas as pd
import pytest

from tracker import analytics, db
from tracker.ledger import record_trade

DAYS = ["2025-01-02", "2025-01-03", "2025-01-06"]
CLOSES = {"AAA": [100.0, 110.0, 99.0], "BBB": [50.0, 50.0, 55.0], "SPY": [400.0, 404.0, 400.0]}


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "t.db")
    db.migrate(c)
    c.executemany("INSERT INTO security (ticker, name, sector, kind) VALUES (?, ?, ?, ?)", [
        ("AAA", "Alpha", "Industrials", "equity"),
        ("BBB", "Beta", "Energy", "equity"),
        ("SPY", "SPY", "Benchmark", "benchmark"),
    ])
    c.executemany(
        "INSERT INTO daily_bar (ticker, bar_date, high, low, close) VALUES (?, ?, ?, ?, ?)",
        [(t, d, px, px, px) for t, series in CLOSES.items() for d, px in zip(DAYS, series)],
    )
    c.commit()
    yield c
    c.close()


def test_position_valuation_and_weights(conn):
    record_trade(conn, "P", "AAA", "buy", 10, 100.0, DAYS[0])
    record_trade(conn, "P", "BBB", "buy", 20, 50.0, DAYS[0])
    rows = {r["ticker"]: r for r in conn.execute("SELECT * FROM v_position_live")}

    assert rows["AAA"]["market_value"] == pytest.approx(990)
    assert rows["AAA"]["unrealized_pnl"] == pytest.approx(-10)
    assert rows["AAA"]["day_pnl"] == pytest.approx(10 * (99 - 110))
    assert rows["BBB"]["market_value"] == pytest.approx(1100)
    assert rows["AAA"]["weight"] + rows["BBB"]["weight"] == pytest.approx(1.0)

    total = conn.execute("SELECT * FROM v_portfolio_live").fetchone()
    assert total["market_value"] == pytest.approx(2090)
    assert total["open_positions"] == 2
    assert total["stale_prices"] == 2   # no intraday quotes, so both priced off EOD


def test_newer_eod_bar_beats_stale_quote(conn):
    conn.execute("INSERT INTO quote VALUES ('AAA', 105.0, 100.0, 0, '2025-01-03T20:00:00+00:00', 'x')")
    p = conn.execute("SELECT price, price_source FROM v_price WHERE ticker = 'AAA'").fetchone()
    assert (p["price"], p["price_source"]) == (99.0, "eod")

    conn.execute("UPDATE quote SET quote_time = '2025-01-06T18:00:00+00:00', price = 101.5")
    p = conn.execute("SELECT price, price_source FROM v_price WHERE ticker = 'AAA'").fetchone()
    assert (p["price"], p["price_source"]) == (101.5, "intraday")


def test_daily_return_ignores_new_money(conn):
    record_trade(conn, "P", "AAA", "buy", 10, 100.0, DAYS[0])
    # Doubling the book on day 2 at the close shouldn't register as a +100% day.
    record_trade(conn, "P", "BBB", "buy", 22, 50.0, DAYS[1])
    daily = pd.read_sql_query("SELECT * FROM v_portfolio_daily ORDER BY bar_date", conn)

    assert daily["net_flow"].tolist() == pytest.approx([1000, 1100, 0])
    assert pd.isna(daily["daily_return"].iloc[0])
    assert daily["daily_return"].iloc[1] == pytest.approx(0.10)
    # day 3: AAA 1100 -> 990, BBB 1100 -> 1210, flat overall
    assert daily["daily_return"].iloc[2] == pytest.approx(0.0)


def test_sell_proceeds_are_a_negative_flow(conn):
    record_trade(conn, "P", "AAA", "buy", 10, 100.0, DAYS[0])
    record_trade(conn, "P", "AAA", "sell", 5, 110.0, DAYS[1])
    daily = pd.read_sql_query("SELECT * FROM v_portfolio_daily ORDER BY bar_date", conn)
    assert daily["net_flow"].iloc[1] == pytest.approx(-550)
    assert daily["daily_return"].iloc[1] == pytest.approx(0.10)


def test_analytics_tables(conn):
    record_trade(conn, "P", "AAA", "buy", 10, 100.0, DAYS[0])
    analytics.refresh_analytics(conn)
    perf = pd.read_sql_query("SELECT * FROM perf_daily ORDER BY bar_date", conn)

    assert perf["twr_index"].tolist() == pytest.approx([1.0, 1.1, 0.99])
    assert perf["drawdown"].tolist() == pytest.approx([0.0, 0.0, 0.99 / 1.1 - 1])
    assert perf["bench_index"].tolist() == pytest.approx([1.0, 1.01, 1.0])

    risk = conn.execute("SELECT * FROM risk_summary").fetchone()
    assert risk["total_return"] == pytest.approx(-0.01)
    assert risk["top5_weight"] == pytest.approx(1.0)
