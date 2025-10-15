-- Reference Data Population Script
-- Financial Portfolio Tracker

-- ========================================
-- POPULATE ASSET CLASSES
-- ========================================
INSERT INTO asset_classes (class_name, description, risk_category) VALUES
('Equities', 'Common stocks and equity securities', 'Aggressive'),
('Fixed Income', 'Bonds and debt securities', 'Conservative'),
('Real Estate', 'REITs and real estate securities', 'Moderate'),
('Commodities', 'Commodity and natural resource securities', 'Aggressive'),
('Cash Equivalents', 'Money market and cash instruments', 'Conservative'),
('Alternative Investments', 'Hedge funds, private equity, derivatives', 'Speculative');

-- ========================================
-- POPULATE SECTORS (GICS SECTORS)
-- ========================================
INSERT INTO sectors (sector_name, sector_code, description) VALUES
('Information Technology', 'IT', 'Software, hardware, semiconductors, and technology services'),
('Healthcare', 'HC', 'Pharmaceuticals, biotechnology, medical devices, and healthcare services'),
('Financials', 'FN', 'Banks, insurance, real estate, and financial services'),
('Consumer Discretionary', 'CD', 'Retail, media, automobiles, and consumer services'),
('Communication Services', 'CS', 'Telecommunications, media, and entertainment'),
('Industrials', 'IN', 'Aerospace, defense, machinery, and transportation'),
('Consumer Staples', 'ST', 'Food, beverages, household products, and personal care'),
('Energy', 'EN', 'Oil, gas, renewable energy, and energy equipment'),
('Utilities', 'UT', 'Electric, gas, water utilities, and renewable energy'),
('Materials', 'MT', 'Chemicals, metals, mining, and paper products');