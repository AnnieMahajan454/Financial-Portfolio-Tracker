from datetime import datetime

import numpy as np
import pandas as pd

from tracker.__main__ import NY, market_is_open
from tracker.marketdata import latest_prints, to_long


def _wide(index, data):
    """Mimic yf.download(..., group_by='column'): columns are (Price, Ticker)."""
    cols = pd.MultiIndex.from_tuples(list(data), names=["Price", "Ticker"])
    return pd.DataFrame(np.array(list(data.values())).T, index=index, columns=cols)


def test_to_long_flattens_and_drops_missing_tickers():
    idx = pd.DatetimeIndex(["2025-01-02", "2025-01-03"], name="Date")
    raw = _wide(idx, {
        ("Close", "AAA"): [10.0, 11.0], ("Close", "BBB"): [np.nan, np.nan],
        ("Adj Close", "AAA"): [9.9, 10.9], ("Adj Close", "BBB"): [np.nan, np.nan],
        ("Volume", "AAA"): [100, 200], ("Volume", "BBB"): [np.nan, np.nan],
    })
    long = to_long(raw)
    assert set(long["ticker"]) == {"AAA"}
    assert {"ts", "ticker", "close", "adj_close", "volume"} <= set(long.columns)
    assert long["close"].tolist() == [10.0, 11.0]


def test_latest_prints_takes_last_session_only():
    ts = pd.to_datetime([
        "2025-01-02 20:59:00+00:00",   # previous session's close
        "2025-01-03 14:30:00+00:00",
        "2025-01-03 14:31:00+00:00",
    ])
    df = pd.DataFrame({"ts": ts, "ticker": "AAA", "close": [9.0, 10.0, 10.5],
                       "volume": [5000, 100, 200]})
    out = latest_prints(df).iloc[0]
    assert out["price"] == 10.5
    assert out["day_volume"] == 300
    assert str(out["session"]) == "2025-01-03"


def test_market_hours():
    def at(y, m, d, hh, mm):
        return datetime(y, m, d, hh, mm, tzinfo=NY)

    assert market_is_open(at(2025, 1, 6, 10, 0))        # Monday morning
    assert not market_is_open(at(2025, 1, 6, 9, 0))     # pre-market
    assert market_is_open(at(2025, 1, 6, 16, 3))        # closing print grace
    assert not market_is_open(at(2025, 1, 4, 12, 0))    # Saturday
