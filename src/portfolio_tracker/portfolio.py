"""
Portfolio Manager for Portfolio Tracker

Handles portfolio operations, performance calculations, and portfolio analytics.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from .database import DatabaseManager
from .data_fetcher import DataFetcher


class PortfolioManager:
    """Manages portfolio operations and analytics."""
    
    def __init__(self, db_manager: DatabaseManager, data_fetcher: DataFetcher):
        """Initialize the portfolio manager.
        
        Args:
            db_manager: Database manager instance
            data_fetcher: Data fetcher instance
        """
        self.db = db_manager
        self.data_fetcher = data_fetcher
        self.logger = logging.getLogger(__name__)
        
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
        return self.db.create_portfolio(user_id, name, description, currency)
    
    def add_holding(self, portfolio_id: int, symbol: str, quantity: float,
                   cost: float, purchase_date: str = None) -> int:
        """Add a holding to portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            symbol: Stock symbol
            quantity: Number of shares
            cost: Average cost per share
            purchase_date: Purchase date
            
        Returns:
            Holding ID
        """
        return self.db.add_holding(portfolio_id, symbol, quantity, cost, purchase_date)
    
    def update_portfolio_prices(self, portfolio_id: int) -> Dict:
        """Update current prices for all holdings in a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Update summary
        """
        # Get all holdings for the portfolio
        holdings = self.db.get_portfolio_holdings(portfolio_id)
        
        if holdings.empty:
            return {'updated': 0, 'message': 'No holdings found'}
        
        symbols = holdings['symbol'].unique().tolist()
        
        # Fetch current prices
        current_prices = self.data_fetcher.get_current_prices(symbols)
        
        updated_count = 0
        for symbol, price in current_prices.items():
            # Update holdings with current price
            query = """
                UPDATE holdings 
                SET current_price = %s,
                    market_value = quantity * %s,
                    unrealized_pnl = (quantity * %s) - (quantity * average_cost),
                    updated_at = CURRENT_TIMESTAMP
                WHERE portfolio_id = %s 
                  AND equity_id = (SELECT equity_id FROM equities WHERE symbol = %s)
            """
            
            rows_updated = self.db.execute_update(query, (price, price, price, portfolio_id, symbol))
            updated_count += rows_updated
        
        # Update portfolio weights
        self._update_portfolio_weights(portfolio_id)
        
        return {
            'updated': updated_count,
            'symbols_processed': len(current_prices),
            'message': f'Updated prices for {updated_count} holdings'
        }
    
    def _update_portfolio_weights(self, portfolio_id: int):
        """Update portfolio weights based on current market values."""
        # Calculate total portfolio value
        total_value_query = """
            SELECT SUM(market_value) as total_value
            FROM holdings 
            WHERE portfolio_id = %s
        """
        
        result = self.db.execute_query(total_value_query, (portfolio_id,))
        total_value = result[0]['total_value'] if result and result[0]['total_value'] else 0
        
        if total_value > 0:
            # Update individual holding weights
            update_weights_query = """
                UPDATE holdings 
                SET weight_percentage = (market_value / %s) * 100
                WHERE portfolio_id = %s
            """
            self.db.execute_update(update_weights_query, (total_value, portfolio_id))
    
    def get_portfolio_performance(self, portfolio_id: int, 
                                 period_days: int = 30) -> Dict:
        """Calculate portfolio performance metrics.
        
        Args:
            portfolio_id: Portfolio ID
            period_days: Performance calculation period
            
        Returns:
            Dictionary with performance metrics
        """
        holdings = self.db.get_portfolio_holdings(portfolio_id)
        
        if holdings.empty:
            return {'error': 'No holdings found'}
        
        # Current portfolio metrics
        total_market_value = holdings['market_value'].sum()
        total_cost = (holdings['quantity'] * holdings['average_cost']).sum()
        total_unrealized_pnl = holdings['unrealized_pnl'].sum()
        
        # Calculate returns
        total_return_pct = (total_unrealized_pnl / total_cost) * 100 if total_cost > 0 else 0
        
        # Get historical performance
        symbols = holdings['symbol'].tolist()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        historical_data = self.data_fetcher.get_bulk_historical_data(symbols, period=f"{period_days}d")
        
        daily_returns = []
        if not historical_data.empty:
            for symbol in symbols:
                symbol_data = historical_data[historical_data['Symbol'] == symbol].copy()
                if not symbol_data.empty:
                    symbol_data = symbol_data.sort_values('Date')
                    symbol_returns = symbol_data['Close'].pct_change().dropna()
                    
                    # Weight returns by holding value
                    holding_weight = holdings[holdings['symbol'] == symbol]['weight_percentage'].iloc[0] / 100
                    weighted_returns = symbol_returns * holding_weight
                    daily_returns.extend(weighted_returns.tolist())
        
        # Calculate volatility and other metrics
        volatility = np.std(daily_returns) * np.sqrt(252) if daily_returns else 0
        
        # Calculate Sharpe ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        avg_return = np.mean(daily_returns) * 252 if daily_returns else 0
        sharpe_ratio = (avg_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        return {
            'portfolio_id': portfolio_id,
            'total_market_value': float(total_market_value),
            'total_cost': float(total_cost),
            'total_unrealized_pnl': float(total_unrealized_pnl),
            'total_return_pct': float(total_return_pct),
            'volatility': float(volatility),
            'sharpe_ratio': float(sharpe_ratio),
            'num_holdings': len(holdings),
            'calculation_date': datetime.now().isoformat()
        }
    
    def get_sector_allocation(self, portfolio_id: int) -> pd.DataFrame:
        """Get portfolio sector allocation.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            DataFrame with sector allocation
        """
        query = """
            SELECT 
                COALESCE(e.sector, 'Unknown') as sector,
                SUM(h.market_value) as sector_value,
                SUM(h.weight_percentage) as sector_weight,
                COUNT(h.holding_id) as num_holdings
            FROM holdings h
            JOIN equities e ON h.equity_id = e.equity_id
            WHERE h.portfolio_id = %s
            GROUP BY e.sector
            ORDER BY sector_value DESC
        """
        
        return self.db.get_dataframe(query, (portfolio_id,))
    
    def get_top_holdings(self, portfolio_id: int, limit: int = 10) -> pd.DataFrame:
        """Get top holdings by market value.
        
        Args:
            portfolio_id: Portfolio ID
            limit: Number of top holdings to return
            
        Returns:
            DataFrame with top holdings
        """
        query = """
            SELECT 
                e.symbol,
                e.company_name,
                e.sector,
                h.quantity,
                h.average_cost,
                h.current_price,
                h.market_value,
                h.unrealized_pnl,
                h.weight_percentage,
                ((h.current_price - h.average_cost) / h.average_cost) * 100 as return_pct
            FROM holdings h
            JOIN equities e ON h.equity_id = e.equity_id
            WHERE h.portfolio_id = %s
            ORDER BY h.market_value DESC
            LIMIT %s
        """
        
        return self.db.get_dataframe(query, (portfolio_id, limit))
    
    def get_performance_attribution(self, portfolio_id: int) -> pd.DataFrame:
        """Calculate performance attribution by holding.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            DataFrame with performance attribution
        """
        query = """
            SELECT 
                e.symbol,
                e.company_name,
                e.sector,
                h.weight_percentage,
                h.unrealized_pnl,
                (h.unrealized_pnl / NULLIF((h.quantity * h.average_cost), 0)) * 100 as holding_return_pct,
                (h.unrealized_pnl / NULLIF((SELECT SUM(quantity * average_cost) FROM holdings WHERE portfolio_id = %s), 0)) * 100 as contribution_to_return
            FROM holdings h
            JOIN equities e ON h.equity_id = e.equity_id
            WHERE h.portfolio_id = %s
            ORDER BY ABS(contribution_to_return) DESC
        """
        
        return self.db.get_dataframe(query, (portfolio_id, portfolio_id))
    
    def rebalance_portfolio(self, portfolio_id: int, 
                          target_weights: Dict[str, float]) -> Dict:
        """Generate rebalancing recommendations.
        
        Args:
            portfolio_id: Portfolio ID
            target_weights: Dictionary of symbol -> target weight
            
        Returns:
            Rebalancing recommendations
        """
        holdings = self.db.get_portfolio_holdings(portfolio_id)
        
        if holdings.empty:
            return {'error': 'No holdings found'}
        
        total_value = holdings['market_value'].sum()
        recommendations = []
        
        for symbol, target_weight in target_weights.items():
            current_holding = holdings[holdings['symbol'] == symbol]
            
            if not current_holding.empty:
                current_weight = current_holding['weight_percentage'].iloc[0]
                current_value = current_holding['market_value'].iloc[0]
                current_price = current_holding['current_price'].iloc[0]
                current_quantity = current_holding['quantity'].iloc[0]
                
                target_value = total_value * (target_weight / 100)
                value_difference = target_value - current_value
                quantity_difference = value_difference / current_price if current_price > 0 else 0
                
                action = 'HOLD'
                if quantity_difference > 0.01:  # Buy threshold
                    action = 'BUY'
                elif quantity_difference < -0.01:  # Sell threshold
                    action = 'SELL'
                
                recommendations.append({
                    'symbol': symbol,
                    'current_weight': float(current_weight),
                    'target_weight': float(target_weight),
                    'current_quantity': float(current_quantity),
                    'recommended_quantity': float(abs(quantity_difference)),
                    'action': action,
                    'estimated_cost': float(abs(value_difference))
                })
        
        return {
            'portfolio_id': portfolio_id,
            'total_portfolio_value': float(total_value),
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat()
        }
    
    def calculate_correlation_matrix(self, portfolio_id: int, 
                                   period: str = "1y") -> pd.DataFrame:
        """Calculate correlation matrix for portfolio holdings.
        
        Args:
            portfolio_id: Portfolio ID
            period: Historical period for correlation calculation
            
        Returns:
            Correlation matrix DataFrame
        """
        holdings = self.db.get_portfolio_holdings(portfolio_id)
        
        if holdings.empty or len(holdings) < 2:
            return pd.DataFrame()
        
        symbols = holdings['symbol'].tolist()
        
        # Get historical data
        historical_data = self.data_fetcher.get_bulk_historical_data(symbols, period=period)
        
        if historical_data.empty:
            return pd.DataFrame()
        
        # Create price matrix
        price_data = {}
        for symbol in symbols:
            symbol_data = historical_data[historical_data['Symbol'] == symbol].copy()
            if not symbol_data.empty:
                symbol_data = symbol_data.sort_values('Date')
                price_data[symbol] = symbol_data.set_index('Date')['Close']
        
        if not price_data:
            return pd.DataFrame()
        
        # Create DataFrame and calculate returns
        price_df = pd.DataFrame(price_data)
        returns_df = price_df.pct_change().dropna()
        
        # Calculate correlation matrix
        correlation_matrix = returns_df.corr()
        
        return correlation_matrix
    
    def export_portfolio_data(self, portfolio_id: int) -> Dict:
        """Export comprehensive portfolio data.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Dictionary with all portfolio data
        """
        # Get basic portfolio info
        summary = self.db.get_portfolio_summary(portfolio_id)
        holdings = self.db.get_portfolio_holdings(portfolio_id)
        performance = self.get_portfolio_performance(portfolio_id)
        sector_allocation = self.get_sector_allocation(portfolio_id)
        
        return {
            'summary': summary,
            'holdings': holdings.to_dict('records') if not holdings.empty else [],
            'performance': performance,
            'sector_allocation': sector_allocation.to_dict('records') if not sector_allocation.empty else [],
            'export_timestamp': datetime.now().isoformat()
        }
