-- Advanced Analytics Views for Portfolio Tracker

-- Portfolio Summary View
CREATE VIEW IF NOT EXISTS portfolio_summary AS
SELECT 
    p.portfolio_id,
    p.name as portfolio_name,
    p.investment_style,
    p.risk_tolerance,
    COUNT(pos.symbol) as total_positions,
    ROUND(SUM(pos.quantity * pos.avg_cost), 2) as total_cost_basis,
    ROUND(SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)), 2) as total_market_value,
    ROUND(SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)) - SUM(pos.quantity * pos.avg_cost), 2) as unrealized_pnl,
    ROUND(CASE WHEN SUM(pos.quantity * pos.avg_cost) > 0 
        THEN ((SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)) / SUM(pos.quantity * pos.avg_cost)) - 1) * 100 
        ELSE 0 END, 2) as total_return_percent,
    p.created_date,
    MAX(pos.last_updated) as last_portfolio_update
FROM portfolios p
LEFT JOIN positions pos ON p.portfolio_id = pos.portfolio_id
LEFT JOIN market_data md ON pos.symbol = md.symbol
GROUP BY p.portfolio_id, p.name, p.investment_style, p.risk_tolerance, p.created_date;

-- Top Holdings View
CREATE VIEW IF NOT EXISTS top_holdings AS
SELECT 
    pos.symbol,
    s.company_name,
    s.sector,
    s.industry,
    SUM(pos.quantity) as total_quantity,
    ROUND(COALESCE(md.price, AVG(pos.avg_cost)), 2) as current_price,
    ROUND(SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)), 2) as total_market_value,
    ROUND(SUM(pos.quantity * pos.avg_cost), 2) as total_cost_basis,
    ROUND(((COALESCE(md.price, AVG(pos.avg_cost)) / AVG(pos.avg_cost)) - 1) * 100, 2) as total_return_percent,
    COUNT(DISTINCT pos.portfolio_id) as held_in_portfolios
FROM positions pos
LEFT JOIN securities s ON pos.symbol = s.symbol
LEFT JOIN market_data md ON pos.symbol = md.symbol
GROUP BY pos.symbol, s.company_name, s.sector, s.industry, md.price
ORDER BY SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)) DESC;

-- Winners and Losers View
CREATE VIEW IF NOT EXISTS winners_losers AS
SELECT 
    pos.symbol,
    s.company_name,
    p.name as portfolio_name,
    ROUND(pos.quantity * pos.avg_cost, 2) as cost_basis,
    ROUND(pos.quantity * COALESCE(md.price, pos.avg_cost), 2) as market_value,
    ROUND(pos.quantity * COALESCE(md.price, pos.avg_cost) - pos.quantity * pos.avg_cost, 2) as unrealized_pnl,
    ROUND(((COALESCE(md.price, pos.avg_cost) / pos.avg_cost) - 1) * 100, 2) as return_percent,
    CASE 
        WHEN ((COALESCE(md.price, pos.avg_cost) / pos.avg_cost) - 1) * 100 > 20 THEN 'Big Winner'
        WHEN ((COALESCE(md.price, pos.avg_cost) / pos.avg_cost) - 1) * 100 > 5 THEN 'Winner'
        WHEN ((COALESCE(md.price, pos.avg_cost) / pos.avg_cost) - 1) * 100 > -5 THEN 'Flat'
        WHEN ((COALESCE(md.price, pos.avg_cost) / pos.avg_cost) - 1) * 100 > -20 THEN 'Loser'
        ELSE 'Big Loser'
    END as performance_category
FROM positions pos
LEFT JOIN securities s ON pos.symbol = s.symbol
LEFT JOIN portfolios p ON pos.portfolio_id = p.portfolio_id
LEFT JOIN market_data md ON pos.symbol = md.symbol
ORDER BY return_percent DESC;

-- Daily P&L View
CREATE VIEW IF NOT EXISTS daily_pnl AS
SELECT 
    p.name as portfolio_name,
    DATE(t.transaction_date) as trade_date,
    t.symbol,
    s.company_name,
    SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity ELSE 0 END) as shares_bought,
    SUM(CASE WHEN t.transaction_type = 'SELL' THEN t.quantity ELSE 0 END) as shares_sold,
    ROUND(SUM(CASE WHEN t.transaction_type = 'BUY' THEN t.quantity * t.price ELSE 0 END), 2) as amount_invested,
    ROUND(SUM(CASE WHEN t.transaction_type = 'SELL' THEN t.quantity * t.price ELSE 0 END), 2) as amount_received,
    ROUND(SUM(CASE WHEN t.transaction_type = 'SELL' THEN t.quantity * t.price ELSE -t.quantity * t.price END), 2) as net_cash_flow
FROM transactions t
LEFT JOIN portfolios p ON t.portfolio_id = p.portfolio_id
LEFT JOIN securities s ON t.symbol = s.symbol
GROUP BY p.name, DATE(t.transaction_date), t.symbol, s.company_name
ORDER BY trade_date DESC;

-- Sector Allocation View
CREATE VIEW IF NOT EXISTS sector_allocation AS
SELECT 
    p.name as portfolio_name,
    s.sector,
    COUNT(pos.symbol) as num_holdings,
    ROUND(SUM(pos.quantity * pos.avg_cost), 2) as sector_cost_basis,
    ROUND(SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)), 2) as sector_market_value,
    ROUND(SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)) / 
          SUM(SUM(pos.quantity * COALESCE(md.price, pos.avg_cost))) OVER (PARTITION BY p.name) * 100, 2) as allocation_percent
FROM positions pos
LEFT JOIN portfolios p ON pos.portfolio_id = p.portfolio_id
LEFT JOIN securities s ON pos.symbol = s.symbol
LEFT JOIN market_data md ON pos.symbol = md.symbol
WHERE s.sector IS NOT NULL
GROUP BY p.name, s.sector
ORDER BY p.name, allocation_percent DESC;

-- Risk Metrics View
CREATE VIEW IF NOT EXISTS risk_metrics AS
SELECT 
    p.name as portfolio_name,
    COUNT(pos.symbol) as total_positions,
    ROUND(AVG(s.beta), 2) as avg_beta,
    ROUND(MAX(pos.quantity * COALESCE(md.price, pos.avg_cost)) / 
          SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)) * 100, 2) as concentration_risk_percent,
    MAX(s.company_name) as largest_holding,
    COUNT(DISTINCT s.sector) as sector_diversification,
    ROUND(STDEV(((COALESCE(md.price, pos.avg_cost) / pos.avg_cost) - 1) * 100), 2) as return_volatility
FROM positions pos
LEFT JOIN portfolios p ON pos.portfolio_id = p.portfolio_id
LEFT JOIN securities s ON pos.symbol = s.symbol
LEFT JOIN market_data md ON pos.symbol = md.symbol
GROUP BY p.name;

-- Portfolio Performance Tracking View
CREATE VIEW IF NOT EXISTS performance_tracking AS
SELECT 
    p.name as portfolio_name,
    DATE('now') as snapshot_date,
    ROUND(SUM(pos.quantity * pos.avg_cost), 2) as cost_basis,
    ROUND(SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)), 2) as market_value,
    ROUND(SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)) - SUM(pos.quantity * pos.avg_cost), 2) as unrealized_pnl,
    ROUND(CASE WHEN SUM(pos.quantity * pos.avg_cost) > 0 
        THEN ((SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)) / SUM(pos.quantity * pos.avg_cost)) - 1) * 100 
        ELSE 0 END, 2) as return_percent,
    MAX(md.timestamp) as last_price_update
FROM portfolios p
LEFT JOIN positions pos ON p.portfolio_id = pos.portfolio_id
LEFT JOIN market_data md ON pos.symbol = md.symbol
GROUP BY p.name;