-- Financial Portfolio Tracker Database Schema
-- Created: October 2024
-- Database: PostgreSQL/SQL Server Compatible

-- ========================================
-- REFERENCE TABLES
-- ========================================

-- Asset Categories and Classifications
CREATE TABLE asset_classes (
    asset_class_id SERIAL PRIMARY KEY,
    class_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    risk_category VARCHAR(20) CHECK (risk_category IN ('Conservative', 'Moderate', 'Aggressive', 'Speculative')),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Market Sectors
CREATE TABLE sectors (
    sector_id SERIAL PRIMARY KEY,
    sector_name VARCHAR(100) UNIQUE NOT NULL,
    sector_code VARCHAR(10),
    description TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exchange Information
CREATE TABLE exchanges (
    exchange_id SERIAL PRIMARY KEY,
    exchange_name VARCHAR(100) UNIQUE NOT NULL,
    exchange_code VARCHAR(10),
    country VARCHAR(50),
    timezone VARCHAR(50),
    trading_hours VARCHAR(100),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Securities Master Table
CREATE TABLE securities (
    security_id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    company_name VARCHAR(200),
    exchange_id INTEGER REFERENCES exchanges(exchange_id),
    sector_id INTEGER REFERENCES sectors(sector_id),
    asset_class_id INTEGER REFERENCES asset_classes(asset_class_id),
    currency VARCHAR(3) DEFAULT 'USD',
    isin VARCHAR(12),
    cusip VARCHAR(10),
    market_cap DECIMAL(20,2),
    shares_outstanding BIGINT,
    ipo_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, exchange_id)
);