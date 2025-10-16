"""
Portfolio Tracker - Core Portfolio Management System
Comprehensive portfolio tracking with real-time market data integration
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from market_data_service import MarketDataService
import logging
from tabulate import tabulate
from colorama import init, Fore, Style
import json
import os

# Initialize colorama for colored output
init()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortfolioTracker:
    """Main portfolio tracking and management system"""
    
    def __init__(self, db_path: str = "portfolio.db"):
        """
        Initialize portfolio tracker with database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.market_service = MarketDataService()
        self.conn = None
        self._connect_db()
        
    def _connect_db(self):
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def create_portfolio(self, name: str, description: str = "", strategy: str = "") -> int:
        """
        Create a new portfolio
        
        Args:
            name: Portfolio name
            description: Portfolio description
            strategy: Investment strategy
            
        Returns:
            Portfolio ID
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO portfolios (name, description, strategy, created_date)
                VALUES (?, ?, ?, ?)
            """, (name, description, strategy, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            portfolio_id = cursor.lastrowid
            self.conn.commit()
            
            logger.info(f"Created portfolio '{name}' with ID {portfolio_id}")
            return portfolio_id
            
        except Exception as e:
            logger.error(f"Error creating portfolio: {e}")
            self.conn.rollback()
            raise
    
    def add_transaction(self, portfolio_name: str, symbol: str, quantity: float, 
                       price: float, transaction_type: str = "BUY") -> int:
        """
        Add a transaction to a portfolio
        
        Args:
            portfolio_name: Name of the portfolio
            symbol: Stock symbol
            quantity: Number of shares
            price: Price per share
            transaction_type: 'BUY' or 'SELL'
            
        Returns:
            Transaction ID
        """
        try:
            # Get portfolio ID
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM portfolios WHERE name = ?", (portfolio_name,))
            portfolio_row = cursor.fetchone()
            
            if not portfolio_row:
                raise ValueError(f"Portfolio '{portfolio_name}' not found")
                
            portfolio_id = portfolio_row['id']
            
            # Ensure security exists
            self._ensure_security_exists(symbol)
            
            # Add transaction
            cursor.execute("""
                INSERT INTO transactions 
                (portfolio_id, symbol, quantity, price, transaction_type, transaction_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (portfolio_id, symbol, quantity, price, transaction_type, 
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            transaction_id = cursor.lastrowid
            self.conn.commit()
            
            # Update positions
            self._update_position(portfolio_id, symbol, quantity, price, transaction_type)
            
            logger.info(f"Added {transaction_type} transaction: {quantity} shares of {symbol} @ ${price}")
            return transaction_id
            
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            self.conn.rollback()
            raise
    
    def _ensure_security_exists(self, symbol: str):
        """Ensure security exists in database, fetch info if needed"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT symbol FROM securities WHERE symbol = ?", (symbol,))
        
        if not cursor.fetchone():
            # Fetch security info from market data service
            info = self.market_service.get_security_info(symbol)
            
            cursor.execute("""
                INSERT INTO securities 
                (symbol, company_name, sector, industry, currency, exchange, market_cap, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (info['symbol'], info['company_name'], info['sector'], 
                  info['industry'], info['currency'], info['exchange'],
                  info['market_cap'], info['description']))
            
            self.conn.commit()
            logger.info(f"Added security info for {symbol}")
    
    def _update_position(self, portfolio_id: int, symbol: str, quantity: float, 
                        price: float, transaction_type: str):
        """Update or create position based on transaction"""
        cursor = self.conn.cursor()
        
        # Get current position
        cursor.execute("""
            SELECT quantity, average_cost FROM positions 
            WHERE portfolio_id = ? AND symbol = ?
        """, (portfolio_id, symbol))
        
        position = cursor.fetchone()
        
        if position:
            # Update existing position
            current_qty = position['quantity']
            current_cost = position['average_cost']
            
            if transaction_type == "BUY":
                new_qty = current_qty + quantity
                new_cost = ((current_qty * current_cost) + (quantity * price)) / new_qty if new_qty > 0 else price
            else:  # SELL
                new_qty = current_qty - quantity
                new_cost = current_cost  # Keep same average cost on sell
            
            if new_qty >= 0:
                cursor.execute("""
                    UPDATE positions 
                    SET quantity = ?, average_cost = ?, last_updated = ?
                    WHERE portfolio_id = ? AND symbol = ?
                """, (new_qty, new_cost, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                      portfolio_id, symbol))
            else:
                logger.warning(f"Sell quantity exceeds position for {symbol}")
        else:
            # Create new position (only for BUY transactions)
            if transaction_type == "BUY":
                cursor.execute("""
                    INSERT INTO positions 
                    (portfolio_id, symbol, quantity, average_cost, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                """, (portfolio_id, symbol, quantity, price, 
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        self.conn.commit()
    
    def update_market_data(self, symbols: List[str] = None):
        """
        Update market data for portfolio securities or specific symbols
        
        Args:
            symbols: List of symbols to update, or None for all portfolio securities
        """
        try:
            if symbols is None:
                # Get all unique symbols from positions
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT symbol FROM positions WHERE quantity > 0
                """)
                symbols = [row['symbol'] for row in cursor.fetchall()]
            
            if not symbols:
                logger.info("No symbols to update")
                return
            
            # Fetch live prices
            prices = self.market_service.get_live_prices(symbols)
            
            # Update market_data table
            cursor = self.conn.cursor()
            for symbol, price in prices.items():
                cursor.execute("""
                    INSERT OR REPLACE INTO market_data 
                    (symbol, price, timestamp, data_source)
                    VALUES (?, ?, ?, 'yahoo_finance')
                """, (symbol, price, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            self.conn.commit()
            logger.info(f"Updated market data for {len(prices)} securities")
            
        except Exception as e:
            logger.error(f"Error updating market data: {e}")
    
    def get_portfolio_summary(self, portfolio_name: str = None) -> pd.DataFrame:
        """
        Get portfolio performance summary
        
        Args:
            portfolio_name: Specific portfolio name, or None for all portfolios
            
        Returns:
            DataFrame with portfolio summary
        """
        try:
            query = """
                SELECT 
                    p.name as Portfolio,
                    COUNT(pos.symbol) as Positions,
                    ROUND(SUM(pos.quantity * pos.average_cost), 2) as Cost_Basis,
                    ROUND(SUM(pos.quantity * COALESCE(md.price, pos.average_cost)), 2) as Market_Value,
                    ROUND(SUM(pos.quantity * COALESCE(md.price, pos.average_cost)) - 
                          SUM(pos.quantity * pos.average_cost), 2) as Unrealized_PL,
                    ROUND(((SUM(pos.quantity * COALESCE(md.price, pos.average_cost)) - 
                           SUM(pos.quantity * pos.average_cost)) / 
                          SUM(pos.quantity * pos.average_cost)) * 100, 1) as Total_Return
                FROM portfolios p
                LEFT JOIN positions pos ON p.id = pos.portfolio_id AND pos.quantity > 0
                LEFT JOIN market_data md ON pos.symbol = md.symbol
                WHERE 1=1
            """
            
            params = []
            if portfolio_name:
                query += " AND p.name = ?"
                params.append(portfolio_name)
            
            query += """
                GROUP BY p.id, p.name
                HAVING COUNT(pos.symbol) > 0
                ORDER BY Market_Value DESC
            """
            
            df = pd.read_sql_query(query, self.conn, params=params)
            return df
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return pd.DataFrame()
    
    def get_top_holdings(self, portfolio_name: str = None, limit: int = 10) -> pd.DataFrame:
        """
        Get top holdings by market value
        
        Args:
            portfolio_name: Specific portfolio name, or None for all
            limit: Number of top holdings to return
            
        Returns:
            DataFrame with top holdings
        """
        try:
            query = """
                SELECT 
                    pos.symbol as Symbol,
                    s.company_name as Company,
                    ROUND(COALESCE(md.price, pos.average_cost), 2) as Live_Price,
                    pos.quantity as Shares,
                    ROUND(pos.quantity * COALESCE(md.price, pos.average_cost), 2) as Market_Value,
                    ROUND(pos.quantity * pos.average_cost, 2) as Cost_Basis,
                    ROUND(((COALESCE(md.price, pos.average_cost) - pos.average_cost) / pos.average_cost) * 100, 1) as Total_Return
                FROM positions pos
                JOIN portfolios p ON pos.portfolio_id = p.id
                JOIN securities s ON pos.symbol = s.symbol
                LEFT JOIN market_data md ON pos.symbol = md.symbol
                WHERE pos.quantity > 0
            """
            
            params = []
            if portfolio_name:
                query += " AND p.name = ?"
                params.append(portfolio_name)
            
            query += """
                ORDER BY Market_Value DESC
                LIMIT ?
            """
            params.append(limit)
            
            df = pd.read_sql_query(query, self.conn, params=params)
            return df
            
        except Exception as e:
            logger.error(f"Error getting top holdings: {e}")
            return pd.DataFrame()
    
    def get_winners_losers(self, portfolio_name: str = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get best and worst performing securities
        
        Args:
            portfolio_name: Specific portfolio name, or None for all
            
        Returns:
            Tuple of (winners_df, losers_df)
        """
        try:
            query = """
                SELECT 
                    pos.symbol as Symbol,
                    s.company_name as Company,
                    ROUND(COALESCE(md.price, pos.average_cost), 2) as Live_Price,
                    ROUND(pos.quantity * COALESCE(md.price, pos.average_cost), 2) as Market_Value,
                    ROUND(((COALESCE(md.price, pos.average_cost) - pos.average_cost) / pos.average_cost) * 100, 1) as Total_Return,
                    ROUND(pos.quantity * (COALESCE(md.price, pos.average_cost) - pos.average_cost), 2) as PL_Amount
                FROM positions pos
                JOIN portfolios p ON pos.portfolio_id = p.id
                JOIN securities s ON pos.symbol = s.symbol
                LEFT JOIN market_data md ON pos.symbol = md.symbol
                WHERE pos.quantity > 0
            """
            
            params = []
            if portfolio_name:
                query += " AND p.name = ?"
                params.append(portfolio_name)
            
            df = pd.read_sql_query(query, self.conn, params=params)
            
            if df.empty:
                return pd.DataFrame(), pd.DataFrame()
            
            # Sort by return percentage
            df = df.sort_values('Total_Return', ascending=False)
            
            # Top 5 winners and losers
            winners = df.head(5)
            losers = df.tail(5)
            
            return winners, losers
            
        except Exception as e:
            logger.error(f"Error getting winners/losers: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def export_portfolio_data(self, portfolio_name: str, export_path: str = "exports/"):
        """
        Export portfolio data to CSV files
        
        Args:
            portfolio_name: Portfolio to export
            export_path: Directory for exports
        """
        try:
            # Create exports directory
            os.makedirs(export_path, exist_ok=True)
            
            # Export summary
            summary = self.get_portfolio_summary(portfolio_name)
            if not summary.empty:
                summary.to_csv(f"{export_path}/{portfolio_name}_summary.csv", index=False)
                
            # Export holdings
            holdings = self.get_top_holdings(portfolio_name, limit=100)
            if not holdings.empty:
                holdings.to_csv(f"{export_path}/{portfolio_name}_holdings.csv", index=False)
                
            # Export transactions
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT t.*, p.name as portfolio_name
                FROM transactions t
                JOIN portfolios p ON t.portfolio_id = p.id
                WHERE p.name = ?
                ORDER BY t.transaction_date DESC
            """, (portfolio_name,))
            
            transactions_df = pd.DataFrame([dict(row) for row in cursor.fetchall()])
            if not transactions_df.empty:
                transactions_df.to_csv(f"{export_path}/{portfolio_name}_transactions.csv", index=False)
                
            logger.info(f"Exported portfolio data to {export_path}")
            
        except Exception as e:
            logger.error(f"Error exporting portfolio data: {e}")
    
    def print_portfolio_report(self, portfolio_name: str = None):
        """Print comprehensive portfolio report with colored output"""
        try:
            print(f"\n{Fore.CYAN}💼 PORTFOLIO PERFORMANCE REPORT{Style.RESET_ALL}")
            print("=" * 70)
            
            # Portfolio Summary
            summary = self.get_portfolio_summary(portfolio_name)
            if not summary.empty:
                print(f"\n{Fore.YELLOW}📊 PORTFOLIO SUMMARY{Style.RESET_ALL}")
                print("-" * 50)
                print(tabulate(summary, headers='keys', tablefmt='grid', floatfmt='.2f'))
                
            # Top Holdings
            holdings = self.get_top_holdings(portfolio_name, limit=8)
            if not holdings.empty:
                print(f"\n{Fore.GREEN}📈 TOP HOLDINGS{Style.RESET_ALL}")
                print("-" * 50)
                print(tabulate(holdings, headers='keys', tablefmt='grid', floatfmt='.2f'))
                
            # Winners and Losers
            winners, losers = self.get_winners_losers(portfolio_name)
            
            if not winners.empty:
                print(f"\n{Fore.GREEN}🔥 TOP PERFORMERS{Style.RESET_ALL}")
                print("-" * 30)
                print(tabulate(winners, headers='keys', tablefmt='simple', floatfmt='.1f'))
                
            if not losers.empty:
                print(f"\n{Fore.RED}❄️  UNDERPERFORMERS{Style.RESET_ALL}")
                print("-" * 30)
                print(tabulate(losers, headers='keys', tablefmt='simple', floatfmt='.1f'))
                
        except Exception as e:
            logger.error(f"Error printing report: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            cursor = self.conn.cursor()
            
            # Count portfolios
            cursor.execute("SELECT COUNT(*) FROM portfolios")
            portfolio_count = cursor.fetchone()[0]
            
            # Count securities
            cursor.execute("SELECT COUNT(*) FROM securities")
            securities_count = cursor.fetchone()[0]
            
            # Count positions
            cursor.execute("SELECT COUNT(*) FROM positions WHERE quantity > 0")
            positions_count = cursor.fetchone()[0]
            
            # Count transactions
            cursor.execute("SELECT COUNT(*) FROM transactions")
            transactions_count = cursor.fetchone()[0]
            
            # Total market value
            cursor.execute("""
                SELECT SUM(pos.quantity * COALESCE(md.price, pos.average_cost))
                FROM positions pos
                LEFT JOIN market_data md ON pos.symbol = md.symbol
                WHERE pos.quantity > 0
            """)
            total_value = cursor.fetchone()[0] or 0
            
            return {
                'portfolios': portfolio_count,
                'securities': securities_count,
                'positions': positions_count,
                'transactions': transactions_count,
                'total_market_value': round(total_value, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

def main():
    """Demo of portfolio tracker functionality"""
    print("💼 Portfolio Tracker Demo")
    print("=" * 50)
    
    # Initialize tracker
    tracker = PortfolioTracker("demo_portfolio.db")
    
    # Create sample portfolio
    portfolio_id = tracker.create_portfolio(
        "Demo Portfolio", 
        "Technology focused growth portfolio",
        "Long-term growth"
    )
    
    # Add sample transactions
    transactions = [
        ("Demo Portfolio", "AAPL", 100, 150.00),
        ("Demo Portfolio", "GOOGL", 25, 2500.00),
        ("Demo Portfolio", "MSFT", 75, 300.00),
        ("Demo Portfolio", "TSLA", 50, 200.00)
    ]
    
    print("\n📝 Adding Transactions...")
    for portfolio, symbol, qty, price in transactions:
        tracker.add_transaction(portfolio, symbol, qty, price)
    
    # Update with live market data
    print("\n📡 Updating Market Data...")
    tracker.update_market_data()
    
    # Generate and print report
    tracker.print_portfolio_report("Demo Portfolio")
    
    # Print database stats
    stats = tracker.get_database_stats()
    print(f"\n{Fore.BLUE}📊 DATABASE STATISTICS{Style.RESET_ALL}")
    print("-" * 30)
    for key, value in stats.items():
        print(f"{key.replace('_', ' ').title()}: {value:,}")
    
    # Export data
    print("\n📁 Exporting Data...")
    tracker.export_portfolio_data("Demo Portfolio")
    
    # Close connection
    tracker.close()

if __name__ == "__main__":
    main()