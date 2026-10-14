-- SQLite schema. Safe to re-run: everything is IF NOT EXISTS.
--
-- Dates are stored as ISO-8601 text (YYYY-MM-DD for trading days, full
-- UTC timestamps for intraday quotes) because SQLite has no native date type
-- and ISO strings sort and compare correctly.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS security (
    ticker      TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    sector      TEXT NOT NULL,
    kind        TEXT NOT NULL DEFAULT 'equity' CHECK (kind IN ('equity', 'benchmark')),
    is_active   INTEGER NOT NULL DEFAULT 1,
    added_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS portfolio (
    portfolio_id  INTEGER PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE,
    strategy      TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- The trade ledger is the source of truth. `position` below is derived from it.
CREATE TABLE IF NOT EXISTS trade (
    trade_id      INTEGER PRIMARY KEY,
    portfolio_id  INTEGER NOT NULL REFERENCES portfolio(portfolio_id),
    ticker        TEXT NOT NULL REFERENCES security(ticker),
    trade_date    TEXT NOT NULL,
    side          TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
    qty           REAL NOT NULL CHECK (qty > 0),
    price         REAL NOT NULL CHECK (price > 0),
    fees          REAL NOT NULL DEFAULT 0 CHECK (fees >= 0)
);
CREATE INDEX IF NOT EXISTS ix_trade_portfolio_ticker ON trade(portfolio_id, ticker, trade_date);
CREATE INDEX IF NOT EXISTS ix_trade_ticker_date ON trade(ticker, trade_date);

-- End-of-day bars. `close` is split-adjusted, `adj_close` also adjusts for dividends.
CREATE TABLE IF NOT EXISTS daily_bar (
    ticker     TEXT NOT NULL REFERENCES security(ticker),
    bar_date   TEXT NOT NULL,
    open       REAL,
    high       REAL,
    low        REAL,
    close      REAL NOT NULL,
    adj_close  REAL,
    volume     INTEGER,
    PRIMARY KEY (ticker, bar_date)
) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS ix_daily_bar_date ON daily_bar(bar_date);

-- Latest intraday print per ticker, overwritten on every refresh.
CREATE TABLE IF NOT EXISTS quote (
    ticker      TEXT PRIMARY KEY REFERENCES security(ticker),
    price       REAL NOT NULL,
    prev_close  REAL,
    day_volume  INTEGER,
    quote_time  TEXT NOT NULL,   -- exchange timestamp of the last bar, UTC
    fetched_at  TEXT NOT NULL    -- when we pulled it, UTC
);

CREATE TABLE IF NOT EXISTS position (
    portfolio_id  INTEGER NOT NULL REFERENCES portfolio(portfolio_id),
    ticker        TEXT NOT NULL REFERENCES security(ticker),
    qty           REAL NOT NULL,
    avg_cost      REAL NOT NULL,
    realized_pnl  REAL NOT NULL DEFAULT 0,
    opened_on     TEXT NOT NULL,
    PRIMARY KEY (portfolio_id, ticker)
);

-- Filled by tracker.analytics: cumulative time-weighted return and drawdown,
-- which need a running product that is awkward in portable SQLite.
CREATE TABLE IF NOT EXISTS perf_daily (
    portfolio_id  INTEGER NOT NULL REFERENCES portfolio(portfolio_id),
    bar_date      TEXT NOT NULL,
    market_value  REAL NOT NULL,
    net_flow      REAL NOT NULL,
    daily_return  REAL,
    twr_index     REAL NOT NULL,
    drawdown      REAL NOT NULL,
    bench_index   REAL,
    PRIMARY KEY (portfolio_id, bar_date)
);

CREATE TABLE IF NOT EXISTS risk_summary (
    portfolio_id     INTEGER PRIMARY KEY REFERENCES portfolio(portfolio_id),
    as_of            TEXT NOT NULL,
    days             INTEGER NOT NULL,
    total_return     REAL,
    ann_volatility   REAL,
    sharpe           REAL,
    max_drawdown     REAL,
    beta             REAL,
    top5_weight      REAL
);

-- One row per market data pull so stale or partial refreshes are visible.
CREATE TABLE IF NOT EXISTS fetch_run (
    run_id       INTEGER PRIMARY KEY,
    kind         TEXT NOT NULL CHECK (kind IN ('daily', 'intraday')),
    started_at   TEXT NOT NULL,
    finished_at  TEXT,
    requested    INTEGER NOT NULL,
    received     INTEGER,
    missing      TEXT
);
