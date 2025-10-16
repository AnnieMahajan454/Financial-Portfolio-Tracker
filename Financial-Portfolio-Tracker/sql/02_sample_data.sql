-- Sample Data for Financial Portfolio Tracker Demo

-- Insert sample portfolios
INSERT OR IGNORE INTO portfolios (name, description, investment_style, risk_tolerance) VALUES 
('Conservative Income', 'Dividend-focused portfolio for steady income', 'Income', 'Low'),
('Growth Portfolio', 'Technology and growth stocks for capital appreciation', 'Growth', 'High'),
('Balanced Fund', 'Mix of growth and value stocks with moderate risk', 'Balanced', 'Medium');

-- Insert securities data
INSERT OR IGNORE INTO securities (symbol, company_name, sector, industry, market_cap) VALUES 
('AAPL', 'Apple Inc.', 'Technology', 'Consumer Electronics', 3000000000000),
('GOOGL', 'Alphabet Inc.', 'Communication Services', 'Internet Content & Information', 2100000000000),
('MSFT', 'Microsoft Corporation', 'Technology', 'Software—Infrastructure', 2800000000000),
('TSLA', 'Tesla Inc.', 'Consumer Cyclical', 'Auto Manufacturers', 800000000000),
('META', 'Meta Platforms Inc.', 'Communication Services', 'Internet Content & Information', 1200000000000),
('JNJ', 'Johnson & Johnson', 'Healthcare', 'Drug Manufacturers—General', 450000000000),
('JPM', 'JPMorgan Chase & Co.', 'Financial Services', 'Banks—Diversified', 600000000000),
('PG', 'Procter & Gamble Co.', 'Consumer Defensive', 'Household & Personal Products', 350000000000),
('KO', 'The Coca-Cola Company', 'Consumer Defensive', 'Beverages—Non-Alcoholic', 280000000000),
('VZ', 'Verizon Communications Inc.', 'Communication Services', 'Telecom Services', 180000000000);

-- Sample transactions for Conservative Income Portfolio
INSERT INTO transactions (portfolio_id, symbol, quantity, price, transaction_type, transaction_date) 
SELECT 1, 'JNJ', 200, 180.50, 'BUY', '2024-01-15'
UNION ALL SELECT 1, 'PG', 150, 145.20, 'BUY', '2024-01-20'
UNION ALL SELECT 1, 'KO', 300, 58.75, 'BUY', '2024-02-01'
UNION ALL SELECT 1, 'JPM', 150, 125.30, 'BUY', '2024-02-15'
UNION ALL SELECT 1, 'VZ', 400, 42.15, 'BUY', '2024-03-01';

-- Sample transactions for Growth Portfolio
INSERT INTO transactions (portfolio_id, symbol, quantity, price, transaction_type, transaction_date)
SELECT 2, 'AAPL', 100, 150.00, 'BUY', '2024-01-10'
UNION ALL SELECT 2, 'GOOGL', 25, 2800.00, 'BUY', '2024-01-15'  
UNION ALL SELECT 2, 'MSFT', 75, 300.00, 'BUY', '2024-01-25'
UNION ALL SELECT 2, 'TSLA', 80, 200.00, 'BUY', '2024-02-05'
UNION ALL SELECT 2, 'META', 70, 180.00, 'BUY', '2024-02-10'
UNION ALL SELECT 2, 'AAPL', 25, 160.00, 'SELL', '2024-03-01'
UNION ALL SELECT 2, 'TSLA', 30, 180.00, 'SELL', '2024-03-15';

-- Update positions based on transactions
INSERT OR REPLACE INTO positions (portfolio_id, symbol, quantity, avg_cost, last_updated)
SELECT 
  portfolio_id,
  symbol,
  SUM(CASE WHEN transaction_type = 'BUY' THEN quantity ELSE -quantity END) as net_quantity,
  AVG(CASE WHEN transaction_type = 'BUY' THEN price ELSE NULL END) as avg_cost,
  CURRENT_TIMESTAMP
FROM transactions 
GROUP BY portfolio_id, symbol
HAVING net_quantity > 0;