"""
Complete Portfolio Tracker Demo
Sets up database, creates sample portfolios, and demonstrates all features
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random
import os
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from portfolio_tracker import PortfolioTracker
from market_data_service import MarketDataService

def create_database_schema(db_path: str = "portfolio.db"):
    """Create the complete database schema"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Portfolios table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            portfolio_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            investment_style TEXT DEFAULT 'Growth',
            risk_tolerance TEXT DEFAULT 'Medium',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Securities table
    cursor.execute("""
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
        )
    """)
    
    # Positions table
    cursor.execute("""
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
        )
    """)
    
    # Transactions table
    cursor.execute("""
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
        )
    """)
    
    # Market data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_data (
            symbol TEXT PRIMARY KEY,
            price REAL NOT NULL,
            volume INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source TEXT DEFAULT 'yahoo_finance',
            previous_close REAL,
            day_change REAL,
            day_change_percent REAL
        )
    """)
    
    # Portfolio performance table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_performance (
            performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id INTEGER,
            date DATE,
            total_value REAL,
            total_cost REAL,
            unrealized_pnl REAL,
            daily_return REAL,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios (portfolio_id)
        )
    """)
    
    # Alerts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id INTEGER,
            symbol TEXT,
            alert_type TEXT,
            threshold_value REAL,
            current_value REAL,
            triggered BOOLEAN DEFAULT 0,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios (portfolio_id)
        )
    """)
    
    # User preferences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            preference_id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_name TEXT UNIQUE,
            setting_value TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create analytics views
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS portfolio_summary AS
        SELECT 
            p.portfolio_id,
            p.name as portfolio_name,
            COUNT(pos.symbol) as total_positions,
            SUM(pos.quantity * pos.avg_cost) as total_cost_basis,
            SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)) as total_market_value,
            SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)) - SUM(pos.quantity * pos.avg_cost) as unrealized_pnl,
            CASE WHEN SUM(pos.quantity * pos.avg_cost) > 0 
                THEN ((SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)) / SUM(pos.quantity * pos.avg_cost)) - 1) * 100 
                ELSE 0 END as total_return_percent
        FROM portfolios p
        LEFT JOIN positions pos ON p.portfolio_id = pos.portfolio_id
        LEFT JOIN market_data md ON pos.symbol = md.symbol
        GROUP BY p.portfolio_id, p.name
    """)
    
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS top_holdings AS
        SELECT 
            pos.symbol,
            s.company_name,
            SUM(pos.quantity) as total_quantity,
            COALESCE(md.price, AVG(pos.avg_cost)) as current_price,
            SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)) as total_market_value,
            SUM(pos.quantity * pos.avg_cost) as total_cost_basis,
            ((COALESCE(md.price, AVG(pos.avg_cost)) / AVG(pos.avg_cost)) - 1) * 100 as total_return_percent
        FROM positions pos
        LEFT JOIN securities s ON pos.symbol = s.symbol
        LEFT JOIN market_data md ON pos.symbol = md.symbol
        GROUP BY pos.symbol, s.company_name, md.price
        ORDER BY SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)) DESC
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Database schema created successfully!")

def create_sample_data():
    """Create sample portfolios with realistic data"""
    
    tracker = PortfolioTracker()
    
    # Create portfolios
    portfolios_data = [
        {
            "name": "Conservative Income",
            "description": "Dividend-focused portfolio for steady income",
            "investment_style": "Income",
            "risk_tolerance": "Low"
        },
        {
            "name": "Growth Portfolio", 
            "description": "Technology and growth stocks for capital appreciation",
            "investment_style": "Growth",
            "risk_tolerance": "High"
        }
    ]
    
    for portfolio in portfolios_data:
        tracker.create_portfolio(**portfolio)
    
    # Sample transactions for Conservative Income Portfolio
    conservative_transactions = [
        ("JNJ", 200, 180.50, "BUY"),
        ("PG", 150, 145.20, "BUY"), 
        ("KO", 300, 58.75, "BUY"),
        ("JPM", 150, 125.30, "BUY"),
        ("VZ", 400, 42.15, "BUY"),
    ]
    
    for symbol, qty, price, action in conservative_transactions:
        tracker.add_transaction("Conservative Income", symbol, qty, price, action)
    
    # Sample transactions for Growth Portfolio
    growth_transactions = [
        ("AAPL", 100, 150.00, "BUY"),
        ("GOOGL", 25, 2800.00, "BUY"),
        ("MSFT", 75, 300.00, "BUY"), 
        ("TSLA", 80, 200.00, "BUY"),
        ("META", 70, 180.00, "BUY"),
        ("NVDA", 50, 400.00, "BUY"),
        # Add some selling transactions
        ("AAPL", 25, 160.00, "SELL"),
        ("TSLA", 30, 180.00, "SELL"),
    ]
    
    for symbol, qty, price, action in growth_transactions:
        tracker.add_transaction("Growth Portfolio", symbol, qty, price, action)
    
    print("✅ Sample portfolio data created!")

def demonstrate_features():
    """Demonstrate all key features with live data"""
    
    tracker = PortfolioTracker()
    
    print("\n" + "="*60)
    print("🚀 FINANCIAL PORTFOLIO TRACKER - LIVE DEMO")
    print("="*60)
    
    # Update market data
    print("\n📡 Updating live market data...")
    updated_prices = tracker.update_market_data()
    print(f"✅ Updated prices for {len(updated_prices)} securities")
    
    # Portfolio Performance Summary
    print("\n💼 PORTFOLIO PERFORMANCE SUMMARY")
    print("-" * 50)
    summary = tracker.get_portfolio_summary()
    if not summary.empty:
        # Format the display nicely
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)
        print(summary.to_string(index=False))
    else:
        print("No portfolio data available")
    
    # Top Holdings
    print("\n📈 TOP HOLDINGS WITH LIVE PRICES") 
    print("-" * 50)
    top_holdings = tracker.get_top_holdings(limit=10)
    if not top_holdings.empty:
        print(top_holdings.to_string(index=False))
    
    # Individual Portfolio Analysis
    portfolios = ["Conservative Income", "Growth Portfolio"]
    
    for portfolio_name in portfolios:
        print(f"\n🔍 DETAILED ANALYSIS: {portfolio_name.upper()}")
        print("-" * 50)
        
        # Get performance analytics
        analytics = tracker.get_performance_analytics(portfolio_name)
        
        if analytics:
            print(f"💰 Total Cost Basis: ${analytics['total_cost_basis']:,.2f}")
            print(f"📊 Current Market Value: ${analytics['current_market_value']:,.2f}")
            print(f"📈 Unrealized P&L: ${analytics['unrealized_pnl']:,.2f}")
            print(f"🎯 Total Return: {analytics['total_return_percent']:.1f}%")
            print(f"🏢 Number of Positions: {analytics['number_of_positions']}")
            print(f"⭐ Largest Position: {analytics.get('largest_position', 'N/A')}")
        
        # Get detailed positions
        positions = tracker.get_positions_detail(portfolio_name)
        if not positions.empty:
            print(f"\n📋 POSITIONS DETAIL - {portfolio_name}")
            print("-" * 40)
            print(positions[['symbol', 'quantity', 'avg_cost', 'current_price', 'return_percent']].to_string(index=False))
        
        # Export data
        export_success = tracker.export_portfolio_data(portfolio_name, "exports/")
        if export_success:
            print(f"📤 Portfolio data exported to exports/ directory")
    
    # Market Summary
    print("\n🌍 MARKET OVERVIEW")
    print("-" * 50)
    market_service = MarketDataService()
    
    # Get summary for major holdings
    major_symbols = ['AAPL', 'GOOGL', 'MSFT', 'META', 'TSLA', 'JNJ', 'JPM']
    market_summary = market_service.get_market_summary(major_symbols)
    
    if not market_summary.empty:
        # Display key columns
        display_columns = ['Symbol', 'Company', 'Price', 'Market Cap', 'Sector']
        available_columns = [col for col in display_columns if col in market_summary.columns]
        print(market_summary[available_columns].to_string(index=False))
    
    print("\n" + "="*60)
    print("✅ DEMO COMPLETED - All features working successfully!")
    print("📊 Check the exports/ directory for CSV files")
    print("🔄 Market data updates automatically via Yahoo Finance API")
    print("⚡ Ready for Power BI integration!")
    print("="*60)

def run_complete_demo():
    """Run the complete demonstration"""
    
    print("🚀 Starting Financial Portfolio Tracker Demo...")
    print("=" * 50)
    
    # Step 1: Create database
    print("Step 1: Creating database schema...")
    create_database_schema()
    
    # Step 2: Create sample data
    print("Step 2: Creating sample portfolios and transactions...")
    create_sample_data()
    
    # Step 3: Demonstrate features
    print("Step 3: Demonstrating live features...")
    demonstrate_features()
    
    print("\n🎉 Demo completed successfully!")
    print("\nNext Steps:")
    print("1. Check the generated 'portfolio.db' SQLite database")
    print("2. Review exported CSV files in the 'exports/' directory")
    print("3. Connect Power BI to the database for advanced analytics")
    print("4. Customize portfolios and transactions for your needs")

if __name__ == "__main__":
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Create exports directory
    os.makedirs("../exports", exist_ok=True)
    
    # Run the complete demo
    run_complete_demo()