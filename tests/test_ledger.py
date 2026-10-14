import pytest

from tracker import db
from tracker.ledger import LedgerError, Position, record_trade


def test_average_cost_includes_fees():
    p = Position()
    p.apply("BUY", 100, 10.0, 5.0, "2025-01-02")
    p.apply("BUY", 100, 12.0, 5.0, "2025-01-03")
    assert p.qty == 200
    assert p.avg_cost == pytest.approx((1000 + 5 + 1200 + 5) / 200)
    assert p.opened_on == "2025-01-02"


def test_partial_sell_books_realized_pnl_and_keeps_basis():
    p = Position()
    p.apply("BUY", 100, 10.0, 0.0, "2025-01-02")
    p.apply("SELL", 40, 15.0, 2.0, "2025-02-01")
    assert p.qty == 60
    assert p.avg_cost == 10.0
    assert p.realized_pnl == pytest.approx(40 * 5 - 2)


def test_closing_out_resets_basis_for_reentry():
    p = Position()
    p.apply("BUY", 10, 50.0, 0.0, "2025-01-02")
    p.apply("SELL", 10, 40.0, 0.0, "2025-01-10")
    p.apply("BUY", 5, 30.0, 0.0, "2025-02-01")
    assert p.qty == 5
    assert p.avg_cost == 30.0
    assert p.realized_pnl == pytest.approx(-100)
    assert p.opened_on == "2025-02-01"


def test_oversell_rejected():
    p = Position()
    p.apply("BUY", 10, 50.0, 0.0, "2025-01-02")
    with pytest.raises(LedgerError):
        p.apply("SELL", 11, 50.0, 0.0, "2025-01-03")


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "t.db")
    db.migrate(c)
    c.executemany("INSERT INTO security (ticker, name, sector) VALUES (?, ?, ?)",
                  [("AAA", "Alpha", "Industrials"), ("BBB", "Beta", "Energy")])
    c.commit()
    yield c
    c.close()


def test_rejected_trade_leaves_ledger_untouched(conn):
    record_trade(conn, "Test", "AAA", "buy", 10, 100.0, "2025-01-02")
    with pytest.raises(LedgerError):
        record_trade(conn, "Test", "AAA", "sell", 50, 100.0, "2025-01-03")
    assert conn.execute("SELECT COUNT(*) FROM trade").fetchone()[0] == 1
    assert conn.execute("SELECT qty FROM position").fetchone()[0] == 10


def test_backdated_trade_replays_in_date_order(conn):
    record_trade(conn, "Test", "AAA", "buy", 10, 100.0, "2025-03-01")
    # Entered after the March buy but dated earlier. Replay goes by trade date, so the
    # January lot is opened and closed before March, and March sets a fresh basis.
    record_trade(conn, "Test", "AAA", "buy", 10, 80.0, "2025-01-01")
    record_trade(conn, "Test", "AAA", "sell", 10, 90.0, "2025-02-01")
    qty, avg, realized = conn.execute("SELECT qty, avg_cost, realized_pnl FROM position").fetchone()
    assert qty == 10
    assert avg == pytest.approx(100.0)
    assert realized == pytest.approx(100.0)


def test_unknown_ticker_rejected(conn):
    with pytest.raises(LedgerError, match="security master"):
        record_trade(conn, "Test", "ZZZ", "buy", 1, 1.0)
