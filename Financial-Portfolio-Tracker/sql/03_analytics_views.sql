-- Advanced Analytics Views
-- Portfolio Performance and Risk Analytics

-- Current Portfolio Holdings with Market Values
CREATE VIEW vw_current_portfolio_holdings AS
SELECT 
    p.portfolio_id,
    p.portfolio_name,
    s.symbol,
    s.company_name,
    sec.sector_name,
    h.quantity,
    h.average_cost,
    rtp.current_price,
    (h.quantity * h.average_cost) as cost_basis,
    (h.quantity * rtp.current_price) as market_value,
    (h.quantity * rtp.current_price) - (h.quantity * h.average_cost) as unrealized_pnl,
    ((rtp.current_price - h.average_cost) / h.average_cost) * 100 as return_percent,
    rtp.change_percent as day_change_percent
FROM holdings h
JOIN portfolios p ON h.portfolio_id = p.portfolio_id
JOIN securities s ON h.security_id = s.security_id
JOIN real_time_prices rtp ON s.security_id = rtp.security_id
JOIN sectors sec ON s.sector_id = sec.sector_id
WHERE h.is_active = TRUE AND p.is_active = TRUE;