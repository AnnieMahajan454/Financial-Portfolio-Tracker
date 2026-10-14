# Financial Portfolio Tracker

Tracks a universe of 235 US large-cap equities and the portfolios built from
them. A Python job pulls prices from Yahoo Finance during market hours and
writes them to SQLite. SQL views turn the trade ledger into positions, P&L
and daily performance, and a Power BI report sits on top.

```text
Yahoo Finance ──► marketdata.py ──► SQLite ──► SQL views ──► CSV export ──► Power BI
 (1-min + daily     batched,          trades,     valuation,     every refresh
  bars, 235 names)  retried           bars,       TWR, sector,
                                       quotes      52w range
```

Output of `python -m tracker status` after a refresh on 13 Oct 2026, with the
demo book loaded:

```text
      portfolio  names market_value unrealized_pnl unrealized_pct day_pnl day_pct     twr sharpe  max_dd beta
    Core Equity    161    2,829,325        315,508        +12.55%   3,071  +0.11% +14.28%   0.96  -7.70% 0.60
         Growth     44    1,328,014        174,441        +15.12%     -67  -0.01% +17.24%   0.80 -11.26% 1.12
Dividend Income     54    1,005,448         67,908         +7.24%  -2,223  -0.22% +10.80%   0.64  -8.27% 0.16

universe 235 names (231 held) | up 115 / down 118 | 235 live quotes, latest 2026-10-13T19:59:00+00:00
```

## Running it

Python 3.10+.

```sh
pip install -r requirements.txt

python -m tracker init          # create tables + views, load data/universe.csv
python -m tracker backfill      # ~400 days of daily bars for all 235 names + SPY (about 25s)
python -m tracker seed-demo     # optional: three sample portfolios, see below
python -m tracker refresh       # latest prices -> analytics -> exports/powerbi/*.csv
python -m tracker status
```

To keep it current during the trading day, either leave `python -m tracker watch`
running (refreshes every 5 minutes while NYSE is open, plus one pass after the
close), or register a scheduled task on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\schedule_refresh.ps1
```

On Linux/macOS, use cron: `*/15 * * * 1-5 cd /path/to/repo && python -m tracker refresh --market-hours-only`.

Recording your own trades:

```sh
python -m tracker trade "Core Equity" buy MSFT 25 512.40 --date 2026-10-01 --fees 1
python -m tracker import my_trades.csv      # portfolio,ticker,trade_date,side,qty,price[,fees]
```

The Power BI side is set up in [powerbi/README.md](powerbi/README.md).

## Layout

```text
tracker/
  marketdata.py   Yahoo pulls: daily bars and 1-minute bars, batched 80 tickers per request
  ledger.py       trade ledger -> positions (average cost, realized P&L)
  analytics.py    time-weighted return index, drawdown, volatility, Sharpe, beta vs SPY
  export.py       writes the Power BI tables to exports/powerbi/
  demo.py         sample portfolios
  __main__.py     CLI
sql/
  001_schema.sql  tables
  002_views.sql   v_price, v_watchlist, v_position_live, v_portfolio_live,
                  v_sector_exposure, v_portfolio_daily
powerbi/
  queries/        Power Query (M), one file per table
  measures.dax    DAX measures and the date table
data/universe.csv tickers, names, GICS sectors
tests/
```

## How the numbers are worked out

**Prices.** Every refresh does two pulls. Daily bars are topped up from the last
stored date (with a week of overlap, because Yahoo sometimes revises recent
bars). Then 1-minute bars for the current session give each ticker's last
trade. `v_price` uses the intraday quote when it's from the latest session and
falls back to the last daily close otherwise, and labels each price with its
source. That means a ticker that drops out of the intraday feed is still
valued, and shows up as `stale` instead of disappearing. `yf.download` is
called with batches of tickers, not once per symbol. A full refresh of 236
symbols, including the analytics and the export, takes about 25 seconds. Any ticker that comes back empty is retried
once, and the misses are logged in `fetch_run`.

**Positions.** The `trade` table is the source of truth. Positions are rebuilt
by replaying every trade in date order with the average-cost method (fees go into
the cost of buys and are subtracted from sale proceeds). Replaying the whole
ledger each time costs nothing at this size. A back-dated or corrected trade
gets the same treatment as any other, and a sell that would take a position
below zero is rejected without writing anything.

**Performance.** `v_portfolio_daily` marks each portfolio to market every day
from the ledger and the daily closes, then works out a time-weighted return.
That day's net cash flow is taken out before comparing with the previous
day's value, so buying another $100k of stock doesn't show up as a gain.
`analytics.py` chains those returns into an index and computes drawdown,
annualized volatility, Sharpe (4% risk-free) and beta against SPY.

**Why CSV into Power BI.** Power BI Desktop can't read SQLite without a
third-party ODBC driver. Writing the model tables to CSV after each refresh
avoids that. Each file is written to a temp name and then renamed, so Power BI
never reads a half-written file. The ODBC route still works if you want it,
and is described in the Power BI README.

## Demo data

`seed-demo` builds three portfolios: Core Equity ($2.5M, broad), Growth ($1.1M,
tech, communications and consumer discretionary) and Dividend Income ($0.9M,
utilities, staples, energy, REITs, pharma and banks). Between them they hold
231 of the 235 names. Each trade is priced at that stock's actual closing price
on the trade date. Some positions are added to later, some are trimmed and a
few are sold completely, so the realized P&L and cash-flow handling get
exercised. The random seed is fixed, so the same price history always produces
the same book.

## Tests

```sh
python -m pytest
```

The tests run offline against small synthetic datasets. They cover average
cost and realized P&L, rejecting a sell larger than the position, out-of-order
trade entry, valuation and weights, flow-adjusted daily returns, the choice
between the intraday quote and the daily close, and parsing of the yfinance
output.

## Known gaps

- Yahoo's quotes are free and unofficial. For NYSE and Nasdaq they're usually
  within a minute of the tape, but there's no SLA, and yfinance breaks every
  so often when Yahoo changes something.
- Splits: bar prices are split-adjusted but trade quantities aren't, so a
  split in a held name needs a manual adjustment trade.
- Exchange holidays aren't in the market-hours check. On a holiday, refresh
  just re-reads the previous session.
- Tickers change. BK became BNY during this project, and AvalonBay and Equity
  Residential stopped trading in August 2026. `status` warns about any active
  ticker that hasn't had a bar in a week, and that's the cue to edit
  `data/universe.csv`.
- USD only, no cash balances or dividends in the ledger.
