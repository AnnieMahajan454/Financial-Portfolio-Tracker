"""
Portfolio Tracker
Professional portfolio management system with real-time analytics
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import json
from market_data_service import MarketDataService

class PortfolioTracker:
    """
    Professional portfolio management system with real-time market data integration
    and advanced analytics capabilities
    """
    
    def __init__(self, db_path: str = "portfolio.db"):
        """
        Initialize portfolio tracker
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.market_service = MarketDataService(db_path)
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def create_portfolio(self, name: str, description: str = "", 
                        investment_style: str = "Growth", 
                        risk_tolerance: str = "Medium") -> bool:
        """
        Create a new portfolio
        
        Args:
            name: Portfolio name
            description: Portfolio description
            investment_style: Investment strategy (Growth, Value, Income, etc.)
            risk_tolerance: Risk tolerance level (Low, Medium, High)
            
        Returns:
            Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO portfolios 
                (name, description, investment_style, risk_tolerance, created_date)
                VALUES (?, ?, ?, ?, ?)
            """, (name, description, investment_style, risk_tolerance, datetime.now()))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Created portfolio: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating portfolio: {e}")
            return False
    
    def add_transaction(self, portfolio_name: str, symbol: str, quantity: float, 
                       price: float, transaction_type: str, 
                       transaction_date: Optional[datetime] = None) -> bool:
        """
        Add a transaction to portfolio
        
        Args:
            portfolio_name: Name of portfolio
            symbol: Stock symbol
            quantity: Number of shares
            price: Price per share
            transaction_type: BUY or SELL
            transaction_date: Date of transaction (default: now)
            
        Returns:
            Success status
        """
        if transaction_date is None:
            transaction_date = datetime.now()
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get portfolio ID
            cursor.execute("SELECT portfolio_id FROM portfolios WHERE name = ?", (portfolio_name,))
            result = cursor.fetchone()
            
            if not result:
                raise ValueError(f"Portfolio '{portfolio_name}' not found")
                
            portfolio_id = result[0]
            
            # Add transaction
            cursor.execute("""
                INSERT INTO transactions 
                (portfolio_id, symbol, quantity, price, transaction_type, transaction_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (portfolio_id, symbol, quantity, price, transaction_type, transaction_date))
            
            # Update positions
            self._update_position(cursor, portfolio_id, symbol, quantity, 
                                transaction_type, price)
            
            # Add security info if not exists
            company_info = self.market_service.get_company_info(symbol)
            if 'error' not in company_info:
                cursor.execute("""
                    INSERT OR IGNORE INTO securities 
                    (symbol, company_name, sector, industry, market_cap)
                    VALUES (?, ?, ?, ?, ?)
                """, (symbol, company_info.get('company_name', ''),
                     company_info.get('sector', ''),
                     company_info.get('industry', ''),
                     company_info.get('market_cap', 0)))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Added transaction: {transaction_type} {quantity} {symbol} @ ${price}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding transaction: {e}")
            return False
    
    def _update_position(self, cursor, portfolio_id: int, symbol: str, 
                        quantity: float, transaction_type: str, price: float):
        """Update position after transaction"""
        
        # Get current position
        cursor.execute("""
            SELECT quantity, avg_cost FROM positions 
            WHERE portfolio_id = ? AND symbol = ?
        """, (portfolio_id, symbol))
        
        current = cursor.fetchone()
        
        if current:
            current_qty, current_avg_cost = current
            
            if transaction_type == 'BUY':
                new_qty = current_qty + quantity
                new_avg_cost = ((current_qty * current_avg_cost) + (quantity * price)) / new_qty
            else:  # SELL
                new_qty = current_qty - quantity
                new_avg_cost = current_avg_cost  # Keep same average cost
                
            if new_qty <= 0:
                cursor.execute("DELETE FROM positions WHERE portfolio_id = ? AND symbol = ?",
                             (portfolio_id, symbol))
            else:
                cursor.execute("""
                    UPDATE positions 
                    SET quantity = ?, avg_cost = ?, last_updated = ?
                    WHERE portfolio_id = ? AND symbol = ?
                """, (new_qty, new_avg_cost, datetime.now(), portfolio_id, symbol))
        else:
            # New position
            if transaction_type == 'BUY':
                cursor.execute("""
                    INSERT INTO positions 
                    (portfolio_id, symbol, quantity, avg_cost, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                """, (portfolio_id, symbol, quantity, price, datetime.now()))
    
    def get_portfolio_summary(self, portfolio_name: Optional[str] = None) -> pd.DataFrame:
        """
        Get comprehensive portfolio summary
        
        Args:
            portfolio_name: Specific portfolio name (None for all)
            
        Returns:
            DataFrame with portfolio performance summary
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT 
                p.name as Portfolio,
                COUNT(pos.symbol) as Positions,
                PRINTF('$%,.0f', SUM(pos.quantity * pos.avg_cost)) as Cost_Basis,
                PRINTF('$%,.0f', SUM(pos.quantity * COALESCE(md.price, pos.avg_cost))) as Market_Value,
                PRINTF('$%,.0f', SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)) - 
                                SUM(pos.quantity * pos.avg_cost)) as Unrealized_PL,
                PRINTF('%.1f%%', 
                    ((SUM(pos.quantity * COALESCE(md.price, pos.avg_cost)) / 
                      SUM(pos.quantity * pos.avg_cost)) - 1) * 100) as Total_Return
            FROM portfolios p
            LEFT JOIN positions pos ON p.portfolio_id = pos.portfolio_id
            LEFT JOIN market_data md ON pos.symbol = md.symbol
            """
            
            if portfolio_name:
                query += " WHERE p.name = ?"
                df = pd.read_sql_query(query, conn, params=(portfolio_name,))
            else:
                query += " GROUP BY p.portfolio_id, p.name"
                df = pd.read_sql_query(query, conn)
            
            conn.close()
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio summary: {e}")
            return pd.DataFrame()
    
    def get_top_holdings(self, portfolio_name: Optional[str] = None, limit: int = 10) -> pd.DataFrame:
        """
        Get top holdings with live prices
        
        Args:
            portfolio_name: Portfolio name (None for all)
            limit: Number of top holdings to return
            
        Returns:
            DataFrame with top holdings
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT 
                pos.symbol as Symbol,
                s.company_name as Company,
                PRINTF('$%.2f', COALESCE(md.price, pos.avg_cost)) as Live_Price,
                PRINTF('$%,.0f', pos.quantity * COALESCE(md.price, pos.avg_cost)) as Market_Value,
                PRINTF('%.1f%%', 
                    ((COALESCE(md.price, pos.avg_cost) / pos.avg_cost) - 1) * 100) as Total_Return
            FROM positions pos
            LEFT JOIN portfolios p ON pos.portfolio_id = p.portfolio_id
            LEFT JOIN securities s ON pos.symbol = s.symbol
            LEFT JOIN market_data md ON pos.symbol = md.symbol
            """
            
            if portfolio_name:
                query += " WHERE p.name = ?"
                query += f" ORDER BY pos.quantity * COALESCE(md.price, pos.avg_cost) DESC LIMIT {limit}"
                df = pd.read_sql_query(query, conn, params=(portfolio_name,))
            else:
                query += f" ORDER BY pos.quantity * COALESCE(md.price, pos.avg_cost) DESC LIMIT {limit}"
                df = pd.read_sql_query(query, conn)
            
            conn.close()
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting top holdings: {e}")
            return pd.DataFrame()
    
    def update_market_data(self) -> Dict[str, float]:
        """
        Update market data for all portfolio positions
        
        Returns:
            Dictionary of updated prices
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all unique symbols from positions
            cursor.execute("SELECT DISTINCT symbol FROM positions")
            symbols = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            if not symbols:
                self.logger.info("No positions found to update")
                return {}
            
            # Update market data
            prices = self.market_service.update_all_market_data(symbols)
            
            self.logger.info(f"Updated market data for {len(prices)} symbols")
            return prices
            
        except Exception as e:
            self.logger.error(f"Error updating market data: {e}")
            return {}
    
    def get_performance_analytics(self, portfolio_name: str, period: str = "1y") -> Dict:
        """
        Get detailed performance analytics
        
        Args:
            portfolio_name: Portfolio name
            period: Analysis period
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get portfolio positions
            query = """
            SELECT pos.symbol, pos.quantity, pos.avg_cost, md.price
            FROM positions pos
            LEFT JOIN portfolios p ON pos.portfolio_id = p.portfolio_id
            LEFT JOIN market_data md ON pos.symbol = md.symbol
            WHERE p.name = ?
            """
            
            positions_df = pd.read_sql_query(query, conn, params=(portfolio_name,))
            conn.close()
            
            if positions_df.empty:
                return {}
            
            # Calculate metrics
            total_cost = (positions_df['quantity'] * positions_df['avg_cost']).sum()
            current_prices = positions_df['price'].fillna(positions_df['avg_cost'])
            total_value = (positions_df['quantity'] * current_prices).sum()
            
            unrealized_pl = total_value - total_cost
            total_return = (unrealized_pl / total_cost * 100) if total_cost > 0 else 0
            
            # Get individual stock returns
            stock_returns = []
            for _, row in positions_df.iterrows():
                symbol = row['symbol']
                returns = self.market_service.calculate_returns(symbol, period)
                if returns:
                    stock_returns.append(returns['total_return'])
            
            avg_stock_return = np.mean(stock_returns) if stock_returns else 0
            portfolio_volatility = np.std(stock_returns) if len(stock_returns) > 1 else 0
            
            return {
                'total_cost_basis': total_cost,
                'current_market_value': total_value,
                'unrealized_pnl': unrealized_pl,
                'total_return_percent': total_return,
                'number_of_positions': len(positions_df),
                'average_stock_return': avg_stock_return,
                'portfolio_volatility': portfolio_volatility,
                'largest_position': positions_df.loc[positions_df['quantity'] * current_prices == 
                                                   (positions_df['quantity'] * current_prices).max(), 'symbol'].iloc[0] if not positions_df.empty else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance analytics: {e}")
            return {}
    
    def export_portfolio_data(self, portfolio_name: str, export_path: str = "exports/") -> bool:
        """
        Export portfolio data to CSV files
        
        Args:
            portfolio_name: Portfolio name
            export_path: Export directory path
            
        Returns:
            Success status
        """
        try:
            import os
            os.makedirs(export_path, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Export positions
            positions_df = self.get_positions_detail(portfolio_name)
            positions_file = f"{export_path}{portfolio_name}_positions_{timestamp}.csv"
            positions_df.to_csv(positions_file, index=False)
            
            # Export transactions
            transactions_df = self.get_transaction_history(portfolio_name)
            transactions_file = f"{export_path}{portfolio_name}_transactions_{timestamp}.csv"
            transactions_df.to_csv(transactions_file, index=False)
            
            # Export summary
            summary_df = self.get_portfolio_summary(portfolio_name)
            summary_file = f"{export_path}{portfolio_name}_summary_{timestamp}.csv"
            summary_df.to_csv(summary_file, index=False)
            
            self.logger.info(f"Exported portfolio data to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting portfolio data: {e}")
            return False
    
    def get_positions_detail(self, portfolio_name: str) -> pd.DataFrame:
        """Get detailed positions for a portfolio"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT 
                pos.symbol,
                s.company_name,
                pos.quantity,
                pos.avg_cost,
                md.price as current_price,
                pos.quantity * pos.avg_cost as cost_basis,
                pos.quantity * COALESCE(md.price, pos.avg_cost) as market_value,
                ((COALESCE(md.price, pos.avg_cost) / pos.avg_cost) - 1) * 100 as return_percent
            FROM positions pos
            LEFT JOIN portfolios p ON pos.portfolio_id = p.portfolio_id
            LEFT JOIN securities s ON pos.symbol = s.symbol
            LEFT JOIN market_data md ON pos.symbol = md.symbol
            WHERE p.name = ?
            ORDER BY pos.quantity * COALESCE(md.price, pos.avg_cost) DESC
            """
            
            df = pd.read_sql_query(query, conn, params=(portfolio_name,))
            conn.close()
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting positions detail: {e}")
            return pd.DataFrame()
    
    def get_transaction_history(self, portfolio_name: str) -> pd.DataFrame:
        """Get transaction history for a portfolio"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT 
                t.transaction_date,
                t.symbol,
                t.quantity,
                t.price,
                t.transaction_type,
                t.quantity * t.price as total_value
            FROM transactions t
            LEFT JOIN portfolios p ON t.portfolio_id = p.portfolio_id
            WHERE p.name = ?
            ORDER BY t.transaction_date DESC
            """
            
            df = pd.read_sql_query(query, conn, params=(portfolio_name,))
            conn.close()
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting transaction history: {e}")
            return pd.DataFrame()


if __name__ == "__main__":
    # Demo usage
    tracker = PortfolioTracker()
    
    print("🚀 PORTFOLIO TRACKER DEMO")
    print("=" * 50)
    
    # This would require database setup first
    # See demo_database_setup.py for complete example