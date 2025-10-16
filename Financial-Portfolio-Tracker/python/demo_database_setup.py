"""
Financial Portfolio Tracker - Complete Demo Setup
Creates database, loads sample data, and demonstrates all features with live market data
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random
from portfolio_tracker import PortfolioTracker
from market_data_service import MarketDataService
from tabulate import tabulate
from colorama import init, Fore, Style
import pandas as pd
import time

# Initialize colorama
init()

class FinancialPortfolioDemo:
    """Complete demonstration of the Financial Portfolio Tracker system"""
    
    def __init__(self, db_name: str = "portfolio_tracker.db"):
        """Initialize demo with clean database"""
        self.db_name = db_name
        self.conn = None
        self.tracker = None
        self.market_service = MarketDataService()
        
        # Remove existing database for clean start
        if os.path.exists(db_name):
            os.remove(db_name)
            print(f"🗑️  Removed existing database: {db_name}")
        
        # Create new database with schema
        self._create_database_schema()
        
        # Initialize tracker
        self.tracker = PortfolioTracker(db_name)
        
    def _create_database_schema(self):
        """Create complete database schema with all tables and views"""
        self.conn = sqlite3.connect(self.db_name)
        cursor = self.conn.cursor()
        
        # Create tables
        schema_sql = """
        -- Portfolios table
        CREATE TABLE portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            strategy TEXT,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        );

        -- Securities master table
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

        -- Positions table
        CREATE TABLE positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id INTEGER,
            symbol TEXT,
            quantity DECIMAL(15,4) NOT NULL,
            average_cost DECIMAL(10,4) NOT NULL,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
            FOREIGN KEY (symbol) REFERENCES securities(symbol),
            UNIQUE(portfolio_id, symbol)
        );

        -- Transactions table
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id INTEGER,
            symbol TEXT,
            quantity DECIMAL(15,4) NOT NULL,
            price DECIMAL(10,4) NOT NULL,
            transaction_type TEXT CHECK(transaction_type IN ('BUY', 'SELL')),
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
            FOREIGN KEY (symbol) REFERENCES securities(symbol)
        );

        -- Market data table
        CREATE TABLE market_data (
            symbol TEXT,
            price DECIMAL(10,4) NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            data_source TEXT DEFAULT 'yahoo_finance',
            volume INTEGER,
            PRIMARY KEY (symbol, timestamp),
            FOREIGN KEY (symbol) REFERENCES securities(symbol)
        );

        -- Portfolio performance tracking
        CREATE TABLE portfolio_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id INTEGER,
            date DATE,
            total_value DECIMAL(15,2),
            daily_return DECIMAL(8,4),
            cumulative_return DECIMAL(8,4),
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
            UNIQUE(portfolio_id, date)
        );

        -- Alerts table
        CREATE TABLE alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id INTEGER,
            symbol TEXT,
            alert_type TEXT CHECK(alert_type IN ('PRICE_TARGET', 'STOP_LOSS', 'PERFORMANCE')),
            threshold_value DECIMAL(10,4),
            is_active BOOLEAN DEFAULT 1,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id),
            FOREIGN KEY (symbol) REFERENCES securities(symbol)
        );

        -- User preferences
        CREATE TABLE user_preferences (
            key TEXT PRIMARY KEY,
            value TEXT,
            data_type TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Create indexes for performance
        CREATE INDEX idx_positions_portfolio ON positions(portfolio_id);
        CREATE INDEX idx_positions_symbol ON positions(symbol);
        CREATE INDEX idx_transactions_portfolio ON transactions(portfolio_id);
        CREATE INDEX idx_transactions_symbol ON transactions(symbol);
        CREATE INDEX idx_transactions_date ON transactions(transaction_date);
        CREATE INDEX idx_market_data_symbol ON market_data(symbol);
        CREATE INDEX idx_market_data_timestamp ON market_data(timestamp);
        """
        
        # Execute schema creation
        cursor.executescript(schema_sql)
        
        # Create analytics views
        views_sql = """
        -- Portfolio Summary View
        CREATE VIEW portfolio_summary AS
        SELECT 
            p.name as portfolio_name,
            p.strategy,
            COUNT(pos.symbol) as total_positions,
            SUM(pos.quantity * pos.average_cost) as total_cost_basis,
            SUM(pos.quantity * COALESCE(md.price, pos.average_cost)) as total_market_value,
            SUM(pos.quantity * COALESCE(md.price, pos.average_cost)) - 
                SUM(pos.quantity * pos.average_cost) as unrealized_pnl,
            CASE 
                WHEN SUM(pos.quantity * pos.average_cost) > 0 THEN
                    ((SUM(pos.quantity * COALESCE(md.price, pos.average_cost)) - 
                      SUM(pos.quantity * pos.average_cost)) / 
                     SUM(pos.quantity * pos.average_cost)) * 100
                ELSE 0
            END as total_return_percent
        FROM portfolios p
        LEFT JOIN positions pos ON p.id = pos.portfolio_id AND pos.quantity > 0
        LEFT JOIN (
            SELECT symbol, price, ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY timestamp DESC) as rn
            FROM market_data
        ) md ON pos.symbol = md.symbol AND md.rn = 1
        WHERE p.is_active = 1
        GROUP BY p.id, p.name, p.strategy;

        -- Top Holdings View
        CREATE VIEW top_holdings AS
        SELECT 
            pos.symbol,
            s.company_name,
            s.sector,
            pos.quantity,
            pos.average_cost,
            COALESCE(md.price, pos.average_cost) as current_price,
            pos.quantity * COALESCE(md.price, pos.average_cost) as market_value,
            pos.quantity * pos.average_cost as cost_basis,
            (COALESCE(md.price, pos.average_cost) - pos.average_cost) as price_change,
            CASE 
                WHEN pos.average_cost > 0 THEN
                    ((COALESCE(md.price, pos.average_cost) - pos.average_cost) / pos.average_cost) * 100
                ELSE 0
            END as return_percent,
            p.name as portfolio_name
        FROM positions pos
        JOIN portfolios p ON pos.portfolio_id = p.id
        JOIN securities s ON pos.symbol = s.symbol
        LEFT JOIN (
            SELECT symbol, price, ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY timestamp DESC) as rn
            FROM market_data
        ) md ON pos.symbol = md.symbol AND md.rn = 1
        WHERE pos.quantity > 0 AND p.is_active = 1;

        -- Winners and Losers View
        CREATE VIEW winners_losers AS
        SELECT 
            symbol,
            company_name,
            portfolio_name,
            current_price,
            market_value,
            return_percent,
            CASE 
                WHEN return_percent > 0 THEN 'WINNER'
                WHEN return_percent < 0 THEN 'LOSER'
                ELSE 'NEUTRAL'
            END as performance_category
        FROM top_holdings
        ORDER BY return_percent DESC;

        -- Daily P&L View
        CREATE VIEW daily_pnl AS
        SELECT 
            date(md.timestamp) as trade_date,
            pos.symbol,
            s.company_name,
            pos.quantity,
            md.price,
            pos.quantity * md.price as market_value,
            pos.quantity * pos.average_cost as cost_basis,
            (pos.quantity * md.price) - (pos.quantity * pos.average_cost) as unrealized_pnl,
            p.name as portfolio_name
        FROM market_data md
        JOIN positions pos ON md.symbol = pos.symbol
        JOIN securities s ON pos.symbol = s.symbol
        JOIN portfolios p ON pos.portfolio_id = p.id
        WHERE pos.quantity > 0
        ORDER BY trade_date DESC, unrealized_pnl DESC;
        """
        
        cursor.executescript(views_sql)
        self.conn.commit()
        self.conn.close()
        
        print("✅ Database schema created successfully with 8 tables and 4 analytical views")
    
    def create_sample_portfolios(self):
        """Create diverse sample portfolios with different strategies"""
        portfolios_data = [
            {
                'name': 'Growth Portfolio',
                'description': 'High growth technology and innovation focused investments',
                'strategy': 'Aggressive Growth - Focus on disruptive technology companies'
            },
            {
                'name': 'Conservative Income',
                'description': 'Stable dividend-paying stocks and defensive sectors',  
                'strategy': 'Income Generation - Dividend aristocrats and blue-chip stocks'
            }
        ]
        
        print(f"\n{Fore.CYAN}🏗️  CREATING SAMPLE PORTFOLIOS{Style.RESET_ALL}")
        print("=" * 60)
        
        for portfolio in portfolios_data:
            portfolio_id = self.tracker.create_portfolio(
                portfolio['name'],
                portfolio['description'], 
                portfolio['strategy']
            )
            print(f"✅ Created '{portfolio['name']}' (ID: {portfolio_id})")
    
    def load_sample_transactions(self):
        """Load realistic sample transactions across portfolios"""
        
        # Growth Portfolio - Tech focused
        growth_transactions = [
            # Large tech positions
            ('Growth Portfolio', 'AAPL', 100, 150.00),
            ('Growth Portfolio', 'GOOGL', 50, 2250.00), 
            ('Growth Portfolio', 'MSFT', 75, 280.00),
            ('Growth Portfolio', 'AMZN', 30, 3700.00),
            ('Growth Portfolio', 'TSLA', 80, 160.00),
            ('Growth Portfolio', 'META', 25, 180.00),
        ]
        
        # Conservative Income Portfolio - Dividend focused
        income_transactions = [
            ('Conservative Income', 'JNJ', 200, 160.00),
            ('Conservative Income', 'JPM', 150, 105.00),
            ('Conservative Income', 'WMT', 100, 140.00),
        ]
        
        all_transactions = growth_transactions + income_transactions
        
        print(f"\n{Fore.YELLOW}📝 LOADING SAMPLE TRANSACTIONS{Style.RESET_ALL}")
        print("=" * 60)
        
        for portfolio, symbol, quantity, price in all_transactions:
            transaction_id = self.tracker.add_transaction(portfolio, symbol, quantity, price)
            print(f"✅ {portfolio}: {quantity} shares of {symbol} @ ${price:.2f}")
            time.sleep(0.2)  # Small delay for realistic feel
    
    def update_live_market_data(self):
        """Fetch and update live market data for all positions"""
        print(f"\n{Fore.GREEN}📡 FETCHING LIVE MARKET DATA{Style.RESET_ALL}")
        print("=" * 60)
        
        # Update market data for all positions
        self.tracker.update_market_data()
        
        # Show updated prices
        cursor = self.tracker.conn.cursor()
        cursor.execute("""
            SELECT md.symbol, s.company_name, md.price, md.timestamp
            FROM market_data md
            JOIN securities s ON md.symbol = s.symbol
            ORDER BY md.timestamp DESC, s.company_name
        """)
        
        market_data = cursor.fetchall()
        
        if market_data:
            print("\n📊 CURRENT MARKET PRICES")
            print("-" * 40)
            
            data = []
            for row in market_data:
                data.append([
                    row[0],  # Symbol
                    row[1][:25] + ('...' if len(row[1]) > 25 else ''),  # Company (truncated)
                    f"${row[2]:.2f}",  # Price
                    row[3].split(' ')[1][:5]  # Time only
                ])
            
            print(tabulate(data, headers=['Symbol', 'Company', 'Live Price', 'Updated'], tablefmt='grid'))
        
        print(f"✅ Updated market data for {len(market_data)} securities")
    
    def generate_comprehensive_reports(self):
        """Generate and display comprehensive portfolio analytics"""
        print(f"\n{Fore.CYAN}🎯 FINANCIAL PORTFOLIO TRACKER - COMPLETE DEMO RESULTS{Style.RESET_ALL}")
        print("=" * 70)
        print(f"{Fore.GREEN}📡 LIVE DATA from Yahoo Finance API{Style.RESET_ALL}")
        print("=" * 70)
        
        # Portfolio Performance Summary
        summary = self.tracker.get_portfolio_summary()
        if not summary.empty:
            print(f"\n{Fore.YELLOW}💼 PORTFOLIO PERFORMANCE SUMMARY{Style.RESET_ALL}")
            print("-" * 50)
            print(tabulate(summary, headers='keys', tablefmt='grid', showindex=False))
        
        # Top Holdings with Live Prices
        holdings = self.tracker.get_top_holdings(limit=10)
        if not holdings.empty:
            print(f"\n{Fore.GREEN}📈 TOP HOLDINGS WITH LIVE PRICES{Style.RESET_ALL}")
            print("-" * 50)
            print(tabulate(holdings, headers='keys', tablefmt='grid', showindex=False))
        
        # Winners and Losers Analysis
        winners, losers = self.tracker.get_winners_losers()
        
        print(f"\n{Fore.CYAN}🏆 WINNERS AND LOSERS{Style.RESET_ALL}")
        print("-" * 50)
        
        if not winners.empty:
            print(f"{Fore.GREEN}🔥 Big Winners:{Style.RESET_ALL}")
            for _, row in winners.head(3).iterrows():
                pnl = row['Market_Value'] - (row['Market_Value'] / (1 + row['Total_Return']/100))
                print(f"   {row['Symbol']}: {row['Total_Return']:.1f}% (${row['Market_Value']:,.0f} P&L)")
        
        if not losers.empty:
            print(f"{Fore.RED}❄️  Losers:{Style.RESET_ALL}")  
            for _, row in losers.tail(3).iterrows():
                pnl = row['Market_Value'] - (row['Market_Value'] / (1 + row['Total_Return']/100))
                print(f"   {row['Symbol']}: {row['Total_Return']:.1f}% (${pnl:,.0f} P&L)")
    
    def display_system_statistics(self):
        """Display comprehensive system statistics"""
        stats = self.tracker.get_database_stats()
        
        print(f"\n{Fore.BLUE}📊 SYSTEM STATISTICS{Style.RESET_ALL}")
        print("-" * 50)
        
        # Get additional stats
        cursor = self.tracker.conn.cursor()
        
        # Days of data
        cursor.execute("SELECT COUNT(DISTINCT DATE(timestamp)) FROM market_data")
        days_of_data = cursor.fetchone()[0]
        
        # Assets under management  
        aum = stats.get('total_market_value', 0)
        
        stats_display = [
            ['Securities Tracked', stats.get('securities', 0)],
            ['Portfolios Managed', stats.get('portfolios', 0)],
            ['Total Positions', stats.get('positions', 0)],
            ['Days of History', days_of_data],
            ['Assets Under Management', f"${aum:,.0f}"]
        ]
        
        print(tabulate(stats_display, headers=['Metric', 'Value'], tablefmt='simple'))
    
    def export_data_for_powerbi(self):
        """Export portfolio data for Power BI integration"""
        print(f"\n{Fore.MAGENTA}📊 PREPARING POWER BI EXPORTS{Style.RESET_ALL}")
        print("-" * 50)
        
        export_path = "exports/"
        os.makedirs(export_path, exist_ok=True)
        
        # Export all portfolio data
        for portfolio_name in ['Growth Portfolio', 'Conservative Income']:
            self.tracker.export_portfolio_data(portfolio_name, export_path)
        
        # Export consolidated analytics data
        cursor = self.tracker.conn.cursor()
        
        # Export portfolio summary view
        summary_df = pd.read_sql_query("SELECT * FROM portfolio_summary", self.tracker.conn)
        summary_df.to_csv(f"{export_path}/portfolio_summary_analytics.csv", index=False)
        
        # Export top holdings view
        holdings_df = pd.read_sql_query("SELECT * FROM top_holdings", self.tracker.conn)
        holdings_df.to_csv(f"{export_path}/top_holdings_analytics.csv", index=False)
        
        # Export market data
        market_df = pd.read_sql_query("""
            SELECT md.symbol, s.company_name, md.price, md.timestamp
            FROM market_data md
            JOIN securities s ON md.symbol = s.symbol
            ORDER BY md.symbol, md.timestamp DESC
        """, self.tracker.conn)
        market_df.to_csv(f"{export_path}/market_data_feed.csv", index=False)
        
        print(f"✅ Exported CSV files to '{export_path}' for Power BI dashboards")
    
    def show_demo_completion(self):
        """Display demo completion summary"""
        print(f"\n{Fore.GREEN}✅ DEMO COMPLETE - FEATURES DEMONSTRATED:{Style.RESET_ALL}")
        print("-" * 50)
        
        features = [
            "🔸 Real-time market data from Yahoo Finance",
            "🔸 Professional portfolio performance tracking", 
            "🔸 Live P&L calculations with unrealized gains/losses",
            "🔸 SQL-based analytics engine",
            "🔸 CSV exports ready for Power BI dashboards",
            "🔸 Complete database with 8 tables and advanced views"
        ]
        
        for feature in features:
            print(feature)
            time.sleep(0.1)
        
        print(f"\n{Fore.CYAN}🎯 Next Steps:{Style.RESET_ALL}")
        print("- Import CSV files into Power BI for advanced visualization")
        print("- Use SQL views for custom analytics and reporting")
        print("- Extend with additional portfolios and securities")
        print("- Set up automated data refresh schedules")
    
    def run_complete_demo(self):
        """Execute the complete portfolio tracking demonstration"""
        print(f"\n{Fore.CYAN}🚀 FINANCIAL PORTFOLIO TRACKER - LIVE DEMO{Style.RESET_ALL}")
        print("=" * 70)
        print("Professional portfolio management with real-time market data")
        print("=" * 70)
        
        # Step 1: Create portfolios
        self.create_sample_portfolios()
        
        # Step 2: Load sample data
        self.load_sample_transactions()
        
        # Step 3: Fetch live market data
        self.update_live_market_data()
        
        # Step 4: Generate comprehensive reports
        self.generate_comprehensive_reports()
        
        # Step 5: Show system statistics
        self.display_system_statistics()
        
        # Step 6: Export data for Power BI
        self.export_data_for_powerbi()
        
        # Step 7: Show completion
        self.show_demo_completion()
        
        # Close connections
        self.tracker.close()

def main():
    """Main demo execution"""
    print("Initializing Financial Portfolio Tracker Demo...")
    
    try:
        # Run complete demonstration
        demo = FinancialPortfolioDemo()
        demo.run_complete_demo()
        
        print(f"\n{Fore.GREEN}🎊 DEMO COMPLETED SUCCESSFULLY!{Style.RESET_ALL}")
        print("\nDatabase: portfolio_tracker.db")
        print("Exports: exports/ directory") 
        print("Ready for Power BI integration and advanced analytics!")
        
    except Exception as e:
        print(f"\n{Fore.RED}❌ Demo failed: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()