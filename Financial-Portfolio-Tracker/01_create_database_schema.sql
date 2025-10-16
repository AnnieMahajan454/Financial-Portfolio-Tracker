-- =====================================================
-- Financial Portfolio Tracker - Database Schema
-- Professional portfolio management system
-- =====================================================

-- Drop existing tables if they exist (for clean reinstall)
DROP TABLE IF EXISTS user_preferences;
DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS portfolio_performance;
DROP TABLE IF EXISTS market_data;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS positions;
DROP TABLE IF EXISTS securities;
DROP TABLE IF EXISTS portfolios;

-- =====================================================
-- CORE TABLES
-- =====================================================

-- Portfolios: Main portfolio definitions
CREATE TABLE portfolios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    strategy TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Securities: Master data for all securities
CREATE TABLE securities (
    symbol TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    sector TEXT,
    industry TEXT,
    currency TEXT DEFAULT 'USD',
    exchange TEXT,
    market_cap INTEGER,
    description TEXT,
    is_active BOOLEAN DEFAULT 1,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Positions: Current portfolio positions
CREATE TABLE positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    quantity DECIMAL(15,4) NOT NULL CHECK(quantity >= 0),
    average_cost DECIMAL(10,4) NOT NULL CHECK(average_cost >= 0),
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE,
    FOREIGN KEY (symbol) REFERENCES securities(symbol) ON DELETE CASCADE,
    UNIQUE(portfolio_id, symbol)
);

-- Transactions: Complete transaction history
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    quantity DECIMAL(15,4) NOT NULL CHECK(quantity > 0),
    price DECIMAL(10,4) NOT NULL CHECK(price > 0),
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('BUY', 'SELL')),
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE,
    FOREIGN KEY (symbol) REFERENCES securities(symbol) ON DELETE CASCADE
);

-- Market Data: Real-time and historical price data
CREATE TABLE market_data (
    symbol TEXT NOT NULL,
    price DECIMAL(10,4) NOT NULL CHECK(price > 0),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_source TEXT DEFAULT 'yahoo_finance',
    volume INTEGER,
    bid DECIMAL(10,4),
    ask DECIMAL(10,4),
    day_high DECIMAL(10,4),
    day_low DECIMAL(10,4),
    PRIMARY KEY (symbol, timestamp),
    FOREIGN KEY (symbol) REFERENCES securities(symbol) ON DELETE CASCADE
);

-- =====================================================
-- PERFORMANCE AND ANALYTICS TABLES  
-- =====================================================

-- Portfolio Performance: Daily performance snapshots
CREATE TABLE portfolio_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER NOT NULL,
    date DATE NOT NULL,
    total_value DECIMAL(15,2) NOT NULL,
    daily_return DECIMAL(8,4),
    cumulative_return DECIMAL(8,4),
    benchmark_return DECIMAL(8,4),
    alpha DECIMAL(8,4),
    beta DECIMAL(8,4),
    sharpe_ratio DECIMAL(8,4),
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE,
    UNIQUE(portfolio_id, date)
);

-- Alerts: Price and performance alerts
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    portfolio_id INTEGER,
    symbol TEXT,
    alert_type TEXT NOT NULL CHECK(alert_type IN ('PRICE_TARGET', 'STOP_LOSS', 'PERFORMANCE')),
    threshold_value DECIMAL(10,4) NOT NULL,
    condition_type TEXT CHECK(condition_type IN ('ABOVE', 'BELOW', 'EQUALS')),
    is_active BOOLEAN DEFAULT 1,
    triggered_date DATETIME,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE,
    FOREIGN KEY (symbol) REFERENCES securities(symbol) ON DELETE CASCADE
);

-- User Preferences: System configuration
CREATE TABLE user_preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    data_type TEXT CHECK(data_type IN ('STRING', 'INTEGER', 'FLOAT', 'BOOLEAN', 'JSON')),
    description TEXT,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =====================================================

-- Position indexes
CREATE INDEX idx_positions_portfolio ON positions(portfolio_id);
CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_positions_quantity ON positions(quantity) WHERE quantity > 0;

-- Transaction indexes
CREATE INDEX idx_transactions_portfolio ON transactions(portfolio_id);
CREATE INDEX idx_transactions_symbol ON transactions(symbol);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);

-- Market data indexes
CREATE INDEX idx_market_data_symbol ON market_data(symbol);
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp);
CREATE INDEX idx_market_data_symbol_time ON market_data(symbol, timestamp DESC);

-- Performance indexes
CREATE INDEX idx_portfolio_performance_date ON portfolio_performance(date);
CREATE INDEX idx_portfolio_performance_portfolio ON portfolio_performance(portfolio_id);

-- Alert indexes
CREATE INDEX idx_alerts_active ON alerts(is_active) WHERE is_active = 1;
CREATE INDEX idx_alerts_portfolio ON alerts(portfolio_id);
CREATE INDEX idx_alerts_symbol ON alerts(symbol);

-- Security indexes
CREATE INDEX idx_securities_sector ON securities(sector);
CREATE INDEX idx_securities_industry ON securities(industry);
CREATE INDEX idx_securities_market_cap ON securities(market_cap);

-- =====================================================
-- TRIGGERS FOR DATA INTEGRITY
-- =====================================================

-- Update last_updated timestamp on position changes
CREATE TRIGGER update_position_timestamp
    AFTER UPDATE ON positions
    FOR EACH ROW
BEGIN
    UPDATE positions 
    SET last_updated = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Update security last_updated timestamp
CREATE TRIGGER update_security_timestamp
    AFTER UPDATE ON securities
    FOR EACH ROW
BEGIN
    UPDATE securities 
    SET last_updated = CURRENT_TIMESTAMP 
    WHERE symbol = NEW.symbol;
END;

-- Validate transaction quantities
CREATE TRIGGER validate_sell_transaction
    BEFORE INSERT ON transactions
    FOR EACH ROW
    WHEN NEW.transaction_type = 'SELL'
BEGIN
    SELECT CASE
        WHEN (SELECT COALESCE(SUM(CASE 
                                    WHEN transaction_type = 'BUY' THEN quantity 
                                    ELSE -quantity 
                                  END), 0)
              FROM transactions 
              WHERE portfolio_id = NEW.portfolio_id 
                AND symbol = NEW.symbol) < NEW.quantity
        THEN RAISE(ABORT, 'Insufficient shares for sell transaction')
    END;
END;

-- =====================================================
-- INITIAL CONFIGURATION DATA
-- =====================================================

-- Insert default user preferences
INSERT INTO user_preferences (key, value, data_type, description) VALUES
('default_currency', 'USD', 'STRING', 'Default currency for portfolio calculations'),
('market_data_refresh_interval', '300', 'INTEGER', 'Market data refresh interval in seconds'),
('enable_alerts', 'true', 'BOOLEAN', 'Enable price and performance alerts'),
('portfolio_view_limit', '50', 'INTEGER', 'Default number of holdings to show in portfolio views'),
('performance_benchmark', 'SPY', 'STRING', 'Default benchmark for performance comparison'),
('risk_free_rate', '0.05', 'FLOAT', 'Risk-free rate for Sharpe ratio calculations'),
('enable_advanced_analytics', 'true', 'BOOLEAN', 'Enable advanced portfolio analytics'),
('export_date_format', '%Y-%m-%d', 'STRING', 'Date format for CSV exports'),
('decimal_precision', '4', 'INTEGER', 'Decimal precision for price calculations'),
('auto_update_securities', 'true', 'BOOLEAN', 'Automatically update security information');

-- =====================================================
-- DATABASE METADATA
-- =====================================================

-- Create metadata table for version tracking
CREATE TABLE schema_metadata (
    version TEXT PRIMARY KEY,
    description TEXT,
    applied_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    checksum TEXT
);

-- Insert schema version
INSERT INTO schema_metadata (version, description, checksum) VALUES
('1.0.0', 'Initial portfolio tracker schema with complete feature set', 'SCHEMA_V1_CHECKSUM');

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

-- Create a simple query to verify schema creation
SELECT 'Portfolio Tracker Database Schema Created Successfully' AS status,
       COUNT(*) AS tables_created
FROM sqlite_master 
WHERE type = 'table' AND name NOT LIKE 'sqlite_%';

-- Display table summary
SELECT 
    'Tables Created:' AS summary,
    GROUP_CONCAT(name, ', ') AS table_names
FROM sqlite_master 
WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
ORDER BY name;