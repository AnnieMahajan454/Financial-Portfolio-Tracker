-- Financial Portfolio Tracker Database Schema
-- Tables for storing portfolio data, equity information, and risk metrics

-- Drop existing tables if they exist (for clean recreation)
DROP TABLE IF EXISTS risk_metrics CASCADE;
DROP TABLE IF EXISTS holdings CASCADE;
DROP TABLE IF EXISTS price_history CASCADE;
DROP TABLE IF EXISTS equities CASCADE;
DROP TABLE IF EXISTS portfolios CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Portfolios table
CREATE TABLE portfolios (
    portfolio_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    portfolio_name VARCHAR(255) NOT NULL,
    description TEXT,
    base_currency VARCHAR(3) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Equities table
CREATE TABLE equities (
    equity_id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    exchange VARCHAR(10),
    currency VARCHAR(3) DEFAULT 'USD',
    market_cap DECIMAL(20, 2),
    beta DECIMAL(8, 4),
    dividend_yield DECIMAL(6, 4),
    pe_ratio DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Price history table
CREATE TABLE price_history (
    price_id SERIAL PRIMARY KEY,
    equity_id INTEGER REFERENCES equities(equity_id) ON DELETE CASCADE,
    price_date DATE NOT NULL,
    open_price DECIMAL(12, 4),
    high_price DECIMAL(12, 4),
    low_price DECIMAL(12, 4),
    close_price DECIMAL(12, 4) NOT NULL,
    adjusted_close DECIMAL(12, 4),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(equity_id, price_date)
);

-- Holdings table
CREATE TABLE holdings (
    holding_id SERIAL PRIMARY KEY,
    portfolio_id INTEGER REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    equity_id INTEGER REFERENCES equities(equity_id) ON DELETE CASCADE,
    quantity DECIMAL(12, 4) NOT NULL,
    average_cost DECIMAL(12, 4) NOT NULL,
    purchase_date DATE,
    current_price DECIMAL(12, 4),
    market_value DECIMAL(15, 2),
    unrealized_pnl DECIMAL(15, 2),
    weight_percentage DECIMAL(6, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(portfolio_id, equity_id)
);

-- Risk metrics table
CREATE TABLE risk_metrics (
    metric_id SERIAL PRIMARY KEY,
    portfolio_id INTEGER REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    equity_id INTEGER REFERENCES equities(equity_id) ON DELETE CASCADE NULL,
    metric_date DATE NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- 'VaR', 'CVaR', 'sharpe_ratio', 'volatility', etc.
    value DECIMAL(15, 6) NOT NULL,
    period_days INTEGER DEFAULT 252, -- calculation period
    confidence_level DECIMAL(5, 4) DEFAULT 0.95, -- for VaR/CVaR
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_portfolio_date (portfolio_id, metric_date),
    INDEX idx_equity_date (equity_id, metric_date),
    INDEX idx_metric_type (metric_type)
);

-- Create indexes for better performance
CREATE INDEX idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX idx_equities_symbol ON equities(symbol);
CREATE INDEX idx_price_history_date ON price_history(price_date);
CREATE INDEX idx_holdings_portfolio ON holdings(portfolio_id);
CREATE INDEX idx_holdings_equity ON holdings(equity_id);

-- Create views for common queries
CREATE VIEW portfolio_summary AS
SELECT 
    p.portfolio_id,
    p.portfolio_name,
    p.user_id,
    COUNT(h.holding_id) as total_holdings,
    SUM(h.market_value) as total_market_value,
    SUM(h.unrealized_pnl) as total_unrealized_pnl,
    AVG(h.weight_percentage) as avg_weight,
    p.base_currency,
    p.updated_at
FROM portfolios p
LEFT JOIN holdings h ON p.portfolio_id = h.portfolio_id
GROUP BY p.portfolio_id, p.portfolio_name, p.user_id, p.base_currency, p.updated_at;

CREATE VIEW equity_performance AS
SELECT 
    e.equity_id,
    e.symbol,
    e.company_name,
    e.sector,
    ph.close_price as current_price,
    ph.price_date as last_updated,
    LAG(ph.close_price, 1) OVER (PARTITION BY e.equity_id ORDER BY ph.price_date) as prev_price,
    ((ph.close_price - LAG(ph.close_price, 1) OVER (PARTITION BY e.equity_id ORDER BY ph.price_date)) / 
     LAG(ph.close_price, 1) OVER (PARTITION BY e.equity_id ORDER BY ph.price_date)) * 100 as daily_return_pct
FROM equities e
JOIN price_history ph ON e.equity_id = ph.equity_id
WHERE ph.price_date = (SELECT MAX(price_date) FROM price_history WHERE equity_id = e.equity_id);

-- Triggers for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_portfolios_updated_at BEFORE UPDATE ON portfolios
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_holdings_updated_at BEFORE UPDATE ON holdings
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_equities_updated_at BEFORE UPDATE ON equities
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
