-- Analytics views. Dropped and recreated on every migrate so edits here take
-- effect without a manual rebuild.

DROP VIEW IF EXISTS v_portfolio_daily;
DROP VIEW IF EXISTS v_sector_exposure;
DROP VIEW IF EXISTS v_portfolio_live;
DROP VIEW IF EXISTS v_position_live;
DROP VIEW IF EXISTS v_watchlist;
DROP VIEW IF EXISTS v_price;
DROP VIEW IF EXISTS v_close_ranked;


CREATE VIEW v_close_ranked AS
SELECT ticker, bar_date, close,
       ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY bar_date DESC) AS rn
FROM daily_bar;


-- Best available price per ticker. The intraday quote wins unless the daily
-- bars are from a later session (e.g. refresh hasn't run since yesterday but a
-- backfill has).
CREATE VIEW v_price AS
WITH last_close AS (
    SELECT ticker,
           MAX(CASE WHEN rn = 1 THEN bar_date END) AS last_date,
           MAX(CASE WHEN rn = 1 THEN close END)    AS last_close,
           MAX(CASE WHEN rn = 2 THEN close END)    AS prior_close
    FROM v_close_ranked
    WHERE rn <= 2
    GROUP BY ticker
)
SELECT s.ticker,
       CASE WHEN q.ticker IS NOT NULL AND date(q.quote_time) >= COALESCE(lc.last_date, '')
            THEN q.price ELSE lc.last_close END                       AS price,
       CASE WHEN q.ticker IS NOT NULL AND date(q.quote_time) >= COALESCE(lc.last_date, '')
            THEN q.prev_close ELSE lc.prior_close END                 AS prev_close,
       CASE WHEN q.ticker IS NOT NULL AND date(q.quote_time) >= COALESCE(lc.last_date, '')
            THEN 'intraday' ELSE 'eod' END                            AS price_source,
       CASE WHEN q.ticker IS NOT NULL AND date(q.quote_time) >= COALESCE(lc.last_date, '')
            THEN q.quote_time ELSE lc.last_date END                   AS price_time,
       q.day_volume
FROM security s
LEFT JOIN quote q       ON q.ticker = s.ticker
LEFT JOIN last_close lc ON lc.ticker = s.ticker;


-- Everything we monitor, held or not.
CREATE VIEW v_watchlist AS
WITH yr AS (
    SELECT ticker,
           MAX(high) AS high_52w,
           MIN(low)  AS low_52w,
           AVG(CASE WHEN bar_date >= date((SELECT MAX(bar_date) FROM daily_bar), '-30 days')
                    THEN volume END) AS avg_volume_30d
    FROM daily_bar
    WHERE bar_date >= date((SELECT MAX(bar_date) FROM daily_bar), '-365 days')
    GROUP BY ticker
)
SELECT s.ticker, s.name, s.sector,
       p.price, p.prev_close,
       p.price - p.prev_close                                   AS day_change,
       (p.price / NULLIF(p.prev_close, 0)) - 1                  AS day_change_pct,
       p.day_volume,
       yr.avg_volume_30d,
       yr.high_52w, yr.low_52w,
       (p.price / NULLIF(yr.high_52w, 0)) - 1                   AS pct_off_high,
       p.price_source, p.price_time,
       EXISTS (SELECT 1 FROM position pos
               WHERE pos.ticker = s.ticker AND pos.qty > 0)     AS is_held
FROM security s
JOIN v_price p ON p.ticker = s.ticker
LEFT JOIN yr   ON yr.ticker = s.ticker
WHERE s.kind = 'equity' AND s.is_active = 1;


-- Closed positions stay in (qty = 0) so realized P&L still adds up.
CREATE VIEW v_position_live AS
SELECT pos.portfolio_id,
       pf.name                                                  AS portfolio,
       pos.ticker, s.name, s.sector,
       pos.qty, pos.avg_cost, pos.opened_on,
       pos.qty * pos.avg_cost                                   AS cost_basis,
       p.price, p.prev_close,
       pos.qty * p.price                                        AS market_value,
       pos.qty * (p.price - pos.avg_cost)                       AS unrealized_pnl,
       CASE WHEN pos.qty > 0 THEN p.price / pos.avg_cost - 1 END AS unrealized_pct,
       pos.qty * (p.price - p.prev_close)                       AS day_pnl,
       (pos.qty * p.price)
           / NULLIF(SUM(pos.qty * p.price) OVER (PARTITION BY pos.portfolio_id), 0)
                                                                AS weight,
       pos.realized_pnl,
       pos.qty > 0                                              AS is_open,
       p.price_source, p.price_time
FROM position pos
JOIN portfolio pf ON pf.portfolio_id = pos.portfolio_id
JOIN security s   ON s.ticker = pos.ticker
JOIN v_price p    ON p.ticker = pos.ticker;


CREATE VIEW v_portfolio_live AS
SELECT portfolio_id, portfolio,
       SUM(is_open)                                             AS open_positions,
       SUM(cost_basis)                                          AS cost_basis,
       SUM(market_value)                                        AS market_value,
       SUM(unrealized_pnl)                                      AS unrealized_pnl,
       SUM(unrealized_pnl) / NULLIF(SUM(cost_basis), 0)         AS unrealized_pct,
       SUM(realized_pnl)                                        AS realized_pnl,
       SUM(day_pnl)                                             AS day_pnl,
       SUM(day_pnl) / NULLIF(SUM(market_value) - SUM(day_pnl), 0) AS day_pct,
       MAX(weight)                                              AS largest_weight,
       SUM(CASE WHEN is_open AND price_source = 'eod' THEN 1 ELSE 0 END) AS stale_prices,
       MAX(price_time)                                          AS priced_as_of
FROM v_position_live
GROUP BY portfolio_id, portfolio;


CREATE VIEW v_sector_exposure AS
SELECT portfolio_id, portfolio, sector,
       COUNT(*)                                                 AS positions,
       SUM(market_value)                                        AS market_value,
       SUM(weight)                                              AS weight,
       SUM(day_pnl)                                             AS day_pnl
FROM v_position_live
WHERE is_open
GROUP BY portfolio_id, portfolio, sector;


-- Daily mark-to-market from the trade ledger and EOD closes.
--
-- daily_return is a time-weighted return: the day's net cash flow (buys minus
-- sell proceeds) is stripped out before comparing with yesterday's value, so
-- adding money to the book doesn't show up as performance. Flows are assumed
-- to land at the close. Trades on non-trading days roll to the next session.
CREATE VIEW v_portfolio_daily AS
WITH days AS (
    SELECT DISTINCT bar_date FROM daily_bar
),
trade_day AS (
    SELECT t.*,
           (SELECT MIN(d.bar_date) FROM days d WHERE d.bar_date >= t.trade_date) AS eff_date
    FROM trade t
),
held AS (
    SELECT d.bar_date, t.portfolio_id, t.ticker,
           SUM(CASE t.side WHEN 'BUY' THEN t.qty ELSE -t.qty END) AS qty
    FROM days d
    JOIN trade_day t ON t.eff_date <= d.bar_date
    GROUP BY d.bar_date, t.portfolio_id, t.ticker
),
mv AS (
    SELECT h.portfolio_id, h.bar_date, SUM(h.qty * b.close) AS market_value
    FROM held h
    JOIN daily_bar b ON b.ticker = h.ticker AND b.bar_date = h.bar_date
    WHERE h.qty > 1e-9
    GROUP BY h.portfolio_id, h.bar_date
),
flow AS (
    SELECT portfolio_id, eff_date AS bar_date,
           SUM(CASE side WHEN 'BUY' THEN qty * price + fees
                         ELSE -(qty * price - fees) END) AS net_flow
    FROM trade_day
    GROUP BY portfolio_id, eff_date
)
SELECT mv.portfolio_id, mv.bar_date, mv.market_value,
       COALESCE(flow.net_flow, 0) AS net_flow,
       (mv.market_value - COALESCE(flow.net_flow, 0))
           / NULLIF(LAG(mv.market_value) OVER w, 0) - 1 AS daily_return
FROM mv
LEFT JOIN flow ON flow.portfolio_id = mv.portfolio_id AND flow.bar_date = mv.bar_date
WINDOW w AS (PARTITION BY mv.portfolio_id ORDER BY mv.bar_date);
