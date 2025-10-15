-- Financial Portfolio Tracker - Analytics Views
-- ==============================================
-- This script creates analytical views for portfolio reporting

-- Portfolio Holdings with Current Prices
DROP VIEW IF EXISTS portfolio_holdings_current;
CREATE VIEW portfolio_holdings_current AS
SELECT 
    p.portfolio_name,
    s.symbol,
    s.security_name,
    s.sector,
    ph.quantity,
    ph.cost_basis_per_share,
    ph.quantity * ph.cost_basis_per_share as cost_basis,
    mp.close_price as current_price,
    ph.quantity * mp.close_price as market_value,
    (ph.quantity * mp.close_price) - (ph.quantity * ph.cost_basis_per_share) as unrealized_pnl,
    CASE 
        WHEN ph.cost_basis_per_share > 0 THEN
            ((mp.close_price - ph.cost_basis_per_share) / ph.cost_basis_per_share) * 100
        ELSE 0 
    END as return_percent
FROM portfolio_holdings ph
JOIN portfolios p ON ph.portfolio_id = p.portfolio_id
JOIN securities s ON ph.security_id = s.security_id
JOIN market_prices mp ON s.security_id = mp.security_id
WHERE mp.price_date = (
    SELECT MAX(price_date) 
    FROM market_prices mp2 
    WHERE mp2.security_id = mp.security_id
);

-- Portfolio Summary
DROP VIEW IF EXISTS portfolio_summary;
CREATE VIEW portfolio_summary AS
SELECT 
    portfolio_name,
    COUNT(*) as position_count,
    SUM(cost_basis) as cost_basis,
    SUM(market_value) as market_value,
    SUM(unrealized_pnl) as unrealized_pnl,
    CASE 
        WHEN SUM(cost_basis) > 0 THEN
            (SUM(unrealized_pnl) / SUM(cost_basis)) * 100
        ELSE 0 
    END as return_percent
FROM portfolio_holdings_current
GROUP BY portfolio_name;