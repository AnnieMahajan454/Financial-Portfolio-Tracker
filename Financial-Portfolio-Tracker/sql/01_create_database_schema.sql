-- Financial Portfolio Tracker - Database Schema
-- ===============================================
-- This script creates the complete database schema for the portfolio tracker

-- Securities reference table
CREATE TABLE IF NOT EXISTS securities (
    security_id INTEGER PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    security_name VARCHAR(100) NOT NULL,
    sector VARCHAR(50),
    market_cap_category VARCHAR(20),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Portfolios table
CREATE TABLE IF NOT EXISTS portfolios (
    portfolio_id INTEGER PRIMARY KEY,
    portfolio_name VARCHAR(100) NOT NULL,
    portfolio_type VARCHAR(50),
    inception_date DATE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Portfolio holdings table
CREATE TABLE IF NOT EXISTS portfolio_holdings (
    holding_id INTEGER PRIMARY KEY,
    portfolio_id INTEGER NOT NULL,
    security_id INTEGER NOT NULL,
    quantity DECIMAL(15,4) NOT NULL,
    cost_basis_per_share DECIMAL(10,4) NOT NULL,
    purchase_date DATE NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id),
    FOREIGN KEY (security_id) REFERENCES securities(security_id)
);

-- Market prices table (for real-time and historical data)
CREATE TABLE IF NOT EXISTS market_prices (
    price_id INTEGER PRIMARY KEY,
    security_id INTEGER NOT NULL,
    price_date DATE NOT NULL,
    open_price DECIMAL(10,4),
    high_price DECIMAL(10,4),
    low_price DECIMAL(10,4),
    close_price DECIMAL(10,4) NOT NULL,
    volume INTEGER,
    updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (security_id) REFERENCES securities(security_id),
    UNIQUE(security_id, price_date)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_portfolio_holdings_portfolio ON portfolio_holdings(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_holdings_security ON portfolio_holdings(security_id);
CREATE INDEX IF NOT EXISTS idx_market_prices_security ON market_prices(security_id);
CREATE INDEX IF NOT EXISTS idx_market_prices_date ON market_prices(price_date);