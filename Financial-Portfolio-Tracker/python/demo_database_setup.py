#!/usr/bin/env python3
"""
Financial Portfolio Tracker - LIVE DEMO Setup
==============================================
This script creates a complete demo database with:
- Real-time market data from Yahoo Finance
- Sample portfolio holdings
- Performance analytics
- Power BI ready CSV exports
"""

import sqlite3
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import sys

def print_header():
    """Print demo header"""
    print("🚀 Financial Portfolio Tracker - LIVE DEMO")
    print("=" * 50)

def create_database_schema(conn):
    """Create database schema"""
    print("🗄️ Creating demo database schema...")
    
    # Read and execute schema
    schema_sql = """
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
    
    -- Market prices table (real-time data)
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
    """
    
    conn.executescript(schema_sql)
    print("✅ Database schema created successfully!")

def insert_reference_data(conn):
    """Insert reference data"""
    print("📝 Inserting reference data...")
    
    # Sample securities
    securities_data = [
        (1, 'AAPL', 'Apple Inc.', 'Technology', 'Large Cap'),
        (2, 'MSFT', 'Microsoft Corporation', 'Technology', 'Large Cap'),
        (3, 'GOOGL', 'Alphabet Inc.', 'Technology', 'Large Cap'),
        (4, 'AMZN', 'Amazon.com Inc.', 'Consumer Discretionary', 'Large Cap'),
        (5, 'TSLA', 'Tesla Inc.', 'Consumer Discretionary', 'Large Cap'),
        (6, 'META', 'Meta Platforms Inc.', 'Technology', 'Large Cap'),
        (7, 'NVDA', 'NVIDIA Corporation', 'Technology', 'Large Cap'),
        (8, 'JPM', 'JPMorgan Chase & Co.', 'Financials', 'Large Cap'),
        (9, 'JNJ', 'Johnson & Johnson', 'Healthcare', 'Large Cap'),
        (10, 'WMT', 'Walmart Inc.', 'Consumer Staples', 'Large Cap')
    ]
    
    conn.executemany("""
        INSERT OR REPLACE INTO securities 
        (security_id, symbol, security_name, sector, market_cap_category) 
        VALUES (?, ?, ?, ?, ?)
    """, securities_data)
    
    # Sample portfolios
    portfolios_data = [
        (1, 'Conservative Income', 'Income', '2023-01-01'),
        (2, 'Growth Portfolio', 'Growth', '2023-01-01')
    ]
    
    conn.executemany("""
        INSERT OR REPLACE INTO portfolios 
        (portfolio_id, portfolio_name, portfolio_type, inception_date) 
        VALUES (?, ?, ?, ?)
    """, portfolios_data)
    
    conn.commit()
    print("✅ Reference data inserted successfully!")

def fetch_market_data(conn):
    """Fetch real-time market data from Yahoo Finance"""
    print("📡 Fetching real-time market data...")
    
    # Get securities list
    cursor = conn.execute("SELECT security_id, symbol FROM securities")
    securities = cursor.fetchall()
    
    for security_id, symbol in securities:
        try:
            # Fetch recent data (last 30 days)
            ticker = yf.Ticker(symbol)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            hist = ticker.history(start=start_date, end=end_date)
            
            if not hist.empty:
                # Get current price
                current_price = hist['Close'].iloc[-1]
                print(f"✅ {symbol}: ${current_price:.2f}")
                
                # Insert price data
                for date, row in hist.iterrows():
                    conn.execute("""
                        INSERT OR REPLACE INTO market_prices 
                        (security_id, price_date, open_price, high_price, low_price, close_price, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        security_id,
                        date.date(),
                        float(row['Open']),
                        float(row['High']),
                        float(row['Low']),
                        float(row['Close']),
                        int(row['Volume']) if pd.notna(row['Volume']) else None
                    ))
            
        except Exception as e:
            print(f"⚠️ Error fetching data for {symbol}: {str(e)}")
    
    conn.commit()
    print("✅ Market data updated successfully!")

def create_sample_holdings(conn):
    """Create sample portfolio holdings"""
    print("💼 Creating sample portfolio holdings...")
    
    # Sample holdings with realistic quantities and costs
    holdings_data = [
        # Conservative Income Portfolio
        (1, 1, 8, 100, 145.50, '2023-06-01'),    # JPM
        (2, 1, 9, 50, 165.25, '2023-06-15'),     # JNJ  
        (3, 1, 10, 200, 155.75, '2023-07-01'),   # WMT
        
        # Growth Portfolio  
        (4, 2, 1, 150, 180.25, '2023-05-01'),    # AAPL
        (5, 2, 2, 80, 310.50, '2023-05-15'),     # MSFT
        (6, 2, 3, 200, 125.75, '2023-06-01'),    # GOOGL
        (7, 2, 4, 75, 140.25, '2023-06-15'),     # AMZN
        (8, 2, 5, 50, 220.50, '2023-07-01'),     # TSLA
        (9, 2, 7, 100, 450.75, '2023-07-15'),    # NVDA
    ]
    
    conn.executemany("""
        INSERT OR REPLACE INTO portfolio_holdings 
        (holding_id, portfolio_id, security_id, quantity, cost_basis_per_share, purchase_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, holdings_data)
    
    conn.commit()
    print("✅ Sample holdings created successfully!")

def create_analytics_views(conn):
    """Create analytics views"""
    print("📊 Creating analytics views...")
    
    analytics_sql = """
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
    """
    
    conn.executescript(analytics_sql)
    print("✅ Analytics views created successfully!")

def export_data_for_powerbi(conn):
    """Export data as CSV files for Power BI"""
    print("📤 Exporting data for Power BI...")
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Export portfolio holdings
    df_holdings = pd.read_sql_query(
        "SELECT * FROM portfolio_holdings_current", 
        conn
    )
    df_holdings.to_csv('data/portfolio_holdings.csv', index=False)
    
    # Export portfolio summary
    df_summary = pd.read_sql_query(
        "SELECT * FROM portfolio_summary", 
        conn
    )
    df_summary.to_csv('data/portfolio_summary.csv', index=False)
    
    # Export sector allocation
    df_sectors = pd.read_sql_query("""
        SELECT 
            portfolio_name,
            sector,
            SUM(market_value) as sector_value,
            COUNT(*) as position_count
        FROM portfolio_holdings_current 
        GROUP BY portfolio_name, sector
    """, conn)
    df_sectors.to_csv('data/sector_allocation.csv', index=False)
    
    # Export price history
    df_prices = pd.read_sql_query("""
        SELECT 
            s.symbol,
            s.security_name,
            mp.price_date,
            mp.close_price
        FROM market_prices mp
        JOIN securities s ON mp.security_id = s.security_id
        ORDER BY s.symbol, mp.price_date
    """, conn)
    df_prices.to_csv('data/price_history.csv', index=False)
    
    print("✅ Data exported successfully!")
    print(f"   - Portfolio Holdings: {len(df_holdings)} records")
    print(f"   - Portfolio Summary: {len(df_summary)} records") 
    print(f"   - Sector Allocation: {len(df_sectors)} records")
    print(f"   - Price History: {len(df_prices)} records")
    
    return df_holdings, df_summary

def display_demo_results(conn):
    """Display formatted demo results"""
    print("\n📊 SAMPLE PORTFOLIO PERFORMANCE:")
    print("=" * 50)
    
    # Portfolio summary
    df_summary = pd.read_sql_query("SELECT * FROM portfolio_summary", conn)
    print(df_summary.to_string(index=False))
    
def main():
    """Main demo function"""
    try:
        print_header()
        
        # Create database connection
        conn = sqlite3.connect('portfolio_tracker_demo.db')
        
        # Setup database
        create_database_schema(conn)
        insert_reference_data(conn)
        fetch_market_data(conn)
        create_sample_holdings(conn)
        create_analytics_views(conn)
        
        # Export and display results
        export_data_for_powerbi(conn)
        display_demo_results(conn)
        
        print("\n🎉 DEMO SETUP COMPLETE!")
        print("=" * 50)
        print("✅ SQLite database created with real market data")
        print("✅ Sample portfolios with live prices")
        print("✅ Analytics views for performance calculations")
        print("✅ CSV files exported for Power BI")
        print("\nYou can now:")
        print("1. View the SQLite database: portfolio_tracker_demo.db")
        print("2. Check CSV files in the 'data' folder")
        print("3. Import CSV files into Power BI Desktop")
        print("4. Create dashboards using the configuration guide")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()