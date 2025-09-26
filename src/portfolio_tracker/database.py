"""
Database Manager for Portfolio Tracker

Handles all database operations including connections, queries, 
and data persistence for the portfolio tracking system.
"""

import os
import logging
import psycopg2
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager
from psycopg2.extras import RealDictCursor, execute_values


class DatabaseManager:
    """Manages database connections and operations for the portfolio tracker."""
    
    def __init__(self, config: Dict[str, str]):
        """Initialize the database manager with configuration.
        
        Args:
            config: Dictionary containing database connection parameters
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def get_connection_string(self) -> str:
        """Build PostgreSQL connection string from config."""
        return (
            f"postgresql://{self.config['user']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
        )
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: Tuple = None) -> List[Dict]:
        """Execute a SELECT query and return results as list of dictionaries.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            List of dictionaries containing query results
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
    
    def execute_update(self, query: str, params: Tuple = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                conn.commit()
                return cur.rowcount
    
    def bulk_insert(self, table: str, data: List[Dict]) -> int:
        """Perform bulk insert operation.
        
        Args:
            table: Target table name
            data: List of dictionaries to insert
            
        Returns:
            Number of inserted rows
        """
        if not data:
            return 0
            
        columns = list(data[0].keys())
        values = [[row[col] for col in columns] for row in data]
        
        query = f"""
            INSERT INTO {table} ({', '.join(columns)})
            VALUES %s
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, query, values)
                conn.commit()
                return cur.rowcount
    
    def get_dataframe(self, query: str, params: Tuple = None) -> pd.DataFrame:
        """Execute query and return results as pandas DataFrame.
        
        Args:
            query: SQL query string
            params: Query parameters tuple
            
        Returns:
            pandas DataFrame containing query results
        """
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)
    
    def create_portfolio(self, user_id: int, name: str, description: str = None, 
                        currency: str = 'USD') -> int:
        """Create a new portfolio.
        
        Args:
            user_id: User ID
            name: Portfolio name
            description: Portfolio description
            currency: Base currency
            
        Returns:
            New portfolio ID
        """
        query = """
            INSERT INTO portfolios (user_id, portfolio_name, description, base_currency)
            VALUES (%s, %s, %s, %s)
            RETURNING portfolio_id
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (user_id, name, description, currency))
                conn.commit()
                return cur.fetchone()[0]
    
    def add_holding(self, portfolio_id: int, symbol: str, quantity: float, 
                   cost: float, purchase_date: str = None) -> int:
        """Add a new holding to a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            symbol: Equity symbol
            quantity: Number of shares
            cost: Average cost per share
            purchase_date: Date of purchase
            
        Returns:
            New holding ID
        """
        # First, ensure equity exists
        equity_id = self.get_or_create_equity(symbol)
        
        query = """
            INSERT INTO holdings (portfolio_id, equity_id, quantity, average_cost, purchase_date)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (portfolio_id, equity_id) 
            DO UPDATE SET 
                quantity = holdings.quantity + EXCLUDED.quantity,
                average_cost = ((holdings.quantity * holdings.average_cost) + 
                              (EXCLUDED.quantity * EXCLUDED.average_cost)) / 
                              (holdings.quantity + EXCLUDED.quantity),
                updated_at = CURRENT_TIMESTAMP
            RETURNING holding_id
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (portfolio_id, equity_id, quantity, cost, purchase_date))
                conn.commit()
                return cur.fetchone()[0]
    
    def get_or_create_equity(self, symbol: str) -> int:
        """Get equity ID by symbol, create if doesn't exist.
        
        Args:
            symbol: Equity symbol
            
        Returns:
            Equity ID
        """
        # First try to get existing
        query = "SELECT equity_id FROM equities WHERE symbol = %s"
        result = self.execute_query(query, (symbol,))
        
        if result:
            return result[0]['equity_id']
        
        # Create new equity record
        query = """
            INSERT INTO equities (symbol, company_name)
            VALUES (%s, %s)
            RETURNING equity_id
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (symbol, f"Company for {symbol}"))
                conn.commit()
                return cur.fetchone()[0]
    
    def update_prices(self, price_data: List[Dict]) -> int:
        """Bulk update price history.
        
        Args:
            price_data: List of dictionaries containing price data
            
        Returns:
            Number of records inserted/updated
        """
        if not price_data:
            return 0
        
        query = """
            INSERT INTO price_history 
            (equity_id, price_date, open_price, high_price, low_price, close_price, volume)
            VALUES %s
            ON CONFLICT (equity_id, price_date)
            DO UPDATE SET
                open_price = EXCLUDED.open_price,
                high_price = EXCLUDED.high_price,
                low_price = EXCLUDED.low_price,
                close_price = EXCLUDED.close_price,
                volume = EXCLUDED.volume
        """
        
        values = [
            (row['equity_id'], row['date'], row['open'], row['high'], 
             row['low'], row['close'], row['volume'])
            for row in price_data
        ]
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                execute_values(cur, query, values)
                conn.commit()
                return cur.rowcount
    
    def get_portfolio_summary(self, portfolio_id: int) -> Dict:
        """Get portfolio summary data.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Dictionary containing portfolio summary
        """
        query = """
            SELECT * FROM portfolio_summary 
            WHERE portfolio_id = %s
        """
        result = self.execute_query(query, (portfolio_id,))
        return result[0] if result else {}
    
    def get_portfolio_holdings(self, portfolio_id: int) -> pd.DataFrame:
        """Get all holdings for a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            DataFrame containing holding details
        """
        query = """
            SELECT 
                h.holding_id,
                e.symbol,
                e.company_name,
                e.sector,
                h.quantity,
                h.average_cost,
                h.current_price,
                h.market_value,
                h.unrealized_pnl,
                h.weight_percentage,
                h.purchase_date
            FROM holdings h
            JOIN equities e ON h.equity_id = e.equity_id
            WHERE h.portfolio_id = %s
            ORDER BY h.market_value DESC
        """
        return self.get_dataframe(query, (portfolio_id,))
    
    def save_risk_metrics(self, metrics: List[Dict]) -> int:
        """Save risk metrics to database.
        
        Args:
            metrics: List of risk metric dictionaries
            
        Returns:
            Number of records inserted
        """
        return self.bulk_insert('risk_metrics', metrics)
