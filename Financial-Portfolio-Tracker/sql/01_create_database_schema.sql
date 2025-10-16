-- Core Database Schema for Financial Portfolio Tracker

-- Portfolios table
CREATE TABLE IF NOT EXISTS portfolios (
  portfolio_id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  investment_style TEXT DEFAULT 'Growth',
  risk_tolerance TEXT DEFAULT 'Medium',
  created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Securities table
CREATE TABLE IF NOT EXISTS securities (
  symbol TEXT PRIMARY KEY,
  company_name TEXT,
  sector TEXT,
  industry TEXT,
  market_cap REAL,
  pe_ratio REAL,
  dividend_yield REAL,
  beta REAL,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Positions table
CREATE TABLE IF NOT EXISTS positions (
  position_id INTEGER PRIMARY KEY AUTOINCREMENT,
  portfolio_id INTEGER,
  symbol TEXT,
  quantity REAL NOT NULL,
  avg_cost REAL NOT NULL,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (portfolio_id) REFERENCES portfolios (portfolio_id),
  FOREIGN KEY (symbol) REFERENCES securities (symbol),
  UNIQUE(portfolio_id, symbol)
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
  transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
  portfolio_id INTEGER,
  symbol TEXT,
  quantity REAL NOT NULL,
  price REAL NOT NULL,
  transaction_type TEXT CHECK(transaction_type IN ('BUY', 'SELL')),
  transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  notes TEXT,
  FOREIGN KEY (portfolio_id) REFERENCES portfolios (portfolio_id)
);

-- Market data table
CREATE TABLE IF NOT EXISTS market_data (
  symbol TEXT PRIMARY KEY,
  price REAL NOT NULL,
  volume INTEGER,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  source TEXT DEFAULT 'yahoo_finance',
  previous_close REAL,
  day_change REAL,
  day_change_percent REAL
);

-- Portfolio performance snapshots
CREATE TABLE IF NOT EXISTS portfolio_performance (
  performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
  portfolio_id INTEGER,
  date DATE,
  total_value REAL,
  total_cost REAL,
  unrealized_pnl REAL,
  daily_return REAL,
  FOREIGN KEY (portfolio_id) REFERENCES portfolios (portfolio_id)
);