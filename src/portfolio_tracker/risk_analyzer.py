"""
Risk Analyzer for Portfolio Tracker

Calculates various risk metrics including VaR, CVaR, Beta, and other 
risk exposure measures for portfolio analysis.
"""

import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from .database import DatabaseManager
from .data_fetcher import DataFetcher


class RiskAnalyzer:
    """Calculates portfolio risk metrics and exposure analysis."""
    
    def __init__(self, db_manager: DatabaseManager, data_fetcher: DataFetcher):
        """Initialize the risk analyzer.
        
        Args:
            db_manager: Database manager instance
            data_fetcher: Data fetcher instance
        """
        self.db = db_manager
        self.data_fetcher = data_fetcher
        self.logger = logging.getLogger(__name__)
        
    def calculate_var(self, returns: pd.Series, confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk (VaR).
        
        Args:
            returns: Series of returns
            confidence_level: Confidence level for VaR calculation
            
        Returns:
            VaR value
        """
        if returns.empty:
            return 0.0
            
        return np.percentile(returns, (1 - confidence_level) * 100)
    
    def calculate_cvar(self, returns: pd.Series, confidence_level: float = 0.95) -> float:
        """Calculate Conditional Value at Risk (CVaR).
        
        Args:
            returns: Series of returns
            confidence_level: Confidence level for CVaR calculation
            
        Returns:
            CVaR value
        """
        if returns.empty:
            return 0.0
            
        var = self.calculate_var(returns, confidence_level)
        return returns[returns <= var].mean()
    
    def calculate_portfolio_beta(self, portfolio_id: int, 
                               benchmark_symbol: str = '^GSPC',
                               period: str = '1y') -> float:
        """Calculate portfolio beta against a benchmark.
        
        Args:
            portfolio_id: Portfolio ID
            benchmark_symbol: Benchmark symbol (default S&P 500)
            period: Time period for calculation
            
        Returns:
            Portfolio beta
        """
        # Get portfolio holdings
        holdings = self.db.get_portfolio_holdings(portfolio_id)
        
        if holdings.empty:
            return 0.0
        
        symbols = holdings['symbol'].tolist()
        
        # Get historical data for portfolio and benchmark
        portfolio_data = self.data_fetcher.get_bulk_historical_data(symbols, period=period)
        benchmark_data = self.data_fetcher.get_historical_data(benchmark_symbol, period=period)
        
        if portfolio_data.empty or benchmark_data.empty:
            return 0.0
        
        # Calculate weighted portfolio returns
        portfolio_returns = self._calculate_weighted_portfolio_returns(
            portfolio_data, holdings, portfolio_id
        )
        
        if portfolio_returns.empty:
            return 0.0
        
        # Calculate benchmark returns
        benchmark_data = benchmark_data.sort_values('Date')
        benchmark_returns = benchmark_data['Close'].pct_change().dropna()
        
        # Align dates and calculate beta
        common_dates = portfolio_returns.index.intersection(benchmark_returns.index)
        
        if len(common_dates) < 30:  # Need sufficient data points
            return 0.0
        
        aligned_portfolio = portfolio_returns.loc[common_dates]
        aligned_benchmark = benchmark_returns.loc[common_dates]
        
        # Calculate beta using linear regression
        covariance = np.cov(aligned_portfolio, aligned_benchmark)[0, 1]
        benchmark_variance = np.var(aligned_benchmark)
        
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 0.0
        
        return float(beta)
    
    def _calculate_weighted_portfolio_returns(self, historical_data: pd.DataFrame,
                                            holdings: pd.DataFrame,
                                            portfolio_id: int) -> pd.Series:
        """Calculate weighted portfolio returns from historical data."""
        if historical_data.empty or holdings.empty:
            return pd.Series()
        
        # Group by date and calculate weighted returns
        portfolio_returns = []
        dates = sorted(historical_data['Date'].unique())
        
        for date in dates:
            daily_data = historical_data[historical_data['Date'] == date]
            weighted_return = 0.0
            
            for _, holding in holdings.iterrows():
                symbol = holding['symbol']
                weight = holding['weight_percentage'] / 100
                
                symbol_data = daily_data[daily_data['Symbol'] == symbol]
                if not symbol_data.empty:
                    # Get previous day's close for return calculation
                    prev_data = historical_data[
                        (historical_data['Symbol'] == symbol) &
                        (historical_data['Date'] < date)
                    ].sort_values('Date')
                    
                    if not prev_data.empty:
                        current_close = symbol_data['Close'].iloc[0]
                        prev_close = prev_data['Close'].iloc[-1]
                        stock_return = (current_close - prev_close) / prev_close
                        weighted_return += weight * stock_return
            
            portfolio_returns.append(weighted_return)
        
        return pd.Series(portfolio_returns, index=dates)
    
    def calculate_portfolio_risk_metrics(self, portfolio_id: int,
                                       confidence_levels: List[float] = [0.95, 0.99]) -> Dict:
        """Calculate comprehensive portfolio risk metrics.
        
        Args:
            portfolio_id: Portfolio ID
            confidence_levels: List of confidence levels for VaR/CVaR
            
        Returns:
            Dictionary with risk metrics
        """
        holdings = self.db.get_portfolio_holdings(portfolio_id)
        
        if holdings.empty:
            return {'error': 'No holdings found'}
        
        symbols = holdings['symbol'].tolist()
        
        # Get historical data (1 year for comprehensive analysis)
        historical_data = self.data_fetcher.get_bulk_historical_data(symbols, period='1y')
        
        if historical_data.empty:
            return {'error': 'No historical data available'}
        
        # Calculate portfolio returns
        portfolio_returns = self._calculate_weighted_portfolio_returns(
            historical_data, holdings, portfolio_id
        )
        
        if portfolio_returns.empty:
            return {'error': 'Could not calculate portfolio returns'}
        
        # Calculate basic risk metrics
        volatility = portfolio_returns.std() * np.sqrt(252)  # Annualized
        mean_return = portfolio_returns.mean() * 252  # Annualized
        
        # Calculate VaR and CVaR for different confidence levels
        var_metrics = {}
        cvar_metrics = {}
        
        for confidence_level in confidence_levels:
            var_daily = self.calculate_var(portfolio_returns, confidence_level)
            cvar_daily = self.calculate_cvar(portfolio_returns, confidence_level)
            
            # Annualize VaR and CVaR
            var_annual = var_daily * np.sqrt(252)
            cvar_annual = cvar_daily * np.sqrt(252)
            
            var_metrics[f'var_{int(confidence_level*100)}'] = float(var_annual)
            cvar_metrics[f'cvar_{int(confidence_level*100)}'] = float(cvar_annual)
        
        # Calculate portfolio beta
        beta = self.calculate_portfolio_beta(portfolio_id)
        
        # Calculate Sharpe ratio
        risk_free_rate = 0.02  # Assume 2% risk-free rate
        sharpe_ratio = (mean_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        # Calculate maximum drawdown
        cumulative_returns = (1 + portfolio_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Calculate Sortino ratio (downside deviation)
        negative_returns = portfolio_returns[portfolio_returns < 0]
        downside_deviation = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
        sortino_ratio = (mean_return - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
        
        # Calculate portfolio concentration metrics
        concentration_metrics = self._calculate_concentration_metrics(holdings)
        
        return {
            'portfolio_id': portfolio_id,
            'calculation_date': datetime.now().isoformat(),
            'basic_metrics': {
                'volatility': float(volatility),
                'mean_return': float(mean_return),
                'beta': float(beta),
                'sharpe_ratio': float(sharpe_ratio),
                'sortino_ratio': float(sortino_ratio),
                'max_drawdown': float(max_drawdown),
            },
            'var_metrics': var_metrics,
            'cvar_metrics': cvar_metrics,
            'concentration_metrics': concentration_metrics,
            'data_points': len(portfolio_returns)
        }
    
    def _calculate_concentration_metrics(self, holdings: pd.DataFrame) -> Dict:
        """Calculate portfolio concentration metrics."""
        if holdings.empty:
            return {}
        
        weights = holdings['weight_percentage'].values / 100
        
        # Herfindahl-Hirschman Index (HHI)
        hhi = np.sum(weights ** 2)
        
        # Effective number of holdings
        effective_holdings = 1 / hhi if hhi > 0 else 0
        
        # Concentration ratio (top 5 holdings)
        top_5_concentration = holdings.nlargest(5, 'weight_percentage')['weight_percentage'].sum()
        
        # Gini coefficient for weight distribution
        sorted_weights = np.sort(weights)
        n = len(sorted_weights)
        cumsum = np.cumsum(sorted_weights)
        gini = (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n if n > 0 else 0
        
        return {
            'herfindahl_index': float(hhi),
            'effective_holdings': float(effective_holdings),
            'top_5_concentration': float(top_5_concentration),
            'gini_coefficient': float(gini),
            'total_holdings': len(holdings)
        }
    
    def calculate_sector_risk_exposure(self, portfolio_id: int) -> pd.DataFrame:
        """Calculate risk exposure by sector.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            DataFrame with sector risk metrics
        """
        query = """
            SELECT 
                COALESCE(e.sector, 'Unknown') as sector,
                SUM(h.weight_percentage) as sector_weight,
                AVG(COALESCE(e.beta, 1.0)) as avg_beta,
                COUNT(h.holding_id) as num_holdings,
                SUM(h.market_value) as sector_value
            FROM holdings h
            JOIN equities e ON h.equity_id = e.equity_id
            WHERE h.portfolio_id = %s
            GROUP BY e.sector
            ORDER BY sector_weight DESC
        """
        
        sector_data = self.db.get_dataframe(query, (portfolio_id,))
        
        if sector_data.empty:
            return pd.DataFrame()
        
        # Calculate sector risk contribution
        sector_data['risk_contribution'] = sector_data['sector_weight'] * sector_data['avg_beta']
        
        return sector_data
    
    def calculate_stress_test_scenarios(self, portfolio_id: int) -> Dict:
        """Calculate portfolio performance under stress scenarios.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Dictionary with stress test results
        """
        holdings = self.db.get_portfolio_holdings(portfolio_id)
        
        if holdings.empty:
            return {'error': 'No holdings found'}
        
        total_value = holdings['market_value'].sum()
        
        # Define stress scenarios
        scenarios = {
            'market_crash_2008': {'market': -0.37, 'tech': -0.45, 'finance': -0.55},
            'covid_crash_2020': {'market': -0.34, 'tech': -0.20, 'finance': -0.45},
            'dot_com_crash_2000': {'market': -0.49, 'tech': -0.78, 'telecom': -0.65},
            'gradual_bear_market': {'market': -0.25, 'all_sectors': -0.20}
        }
        
        results = {}
        
        for scenario_name, scenario_shocks in scenarios.items():
            scenario_loss = 0.0
            
            for _, holding in holdings.iterrows():
                sector = holding.get('sector', 'Unknown').lower()
                weight = holding['weight_percentage'] / 100
                
                # Apply sector-specific shock or general market shock
                shock = 0.0
                for shock_sector, shock_value in scenario_shocks.items():
                    if shock_sector == 'all_sectors' or shock_sector in sector:
                        shock = shock_value
                        break
                    elif shock_sector == 'market':
                        shock = shock_value  # Default market shock
                
                scenario_loss += weight * shock
            
            scenario_value_loss = total_value * abs(scenario_loss)
            
            results[scenario_name] = {
                'portfolio_loss_pct': float(scenario_loss * 100),
                'portfolio_value_loss': float(scenario_value_loss),
                'remaining_value': float(total_value + (total_value * scenario_loss))
            }
        
        return {
            'portfolio_id': portfolio_id,
            'current_portfolio_value': float(total_value),
            'stress_scenarios': results,
            'calculation_date': datetime.now().isoformat()
        }
    
    def save_risk_metrics(self, portfolio_id: int, metrics: Dict) -> int:
        """Save calculated risk metrics to database.
        
        Args:
            portfolio_id: Portfolio ID
            metrics: Risk metrics dictionary
            
        Returns:
            Number of records saved
        """
        metric_records = []
        calculation_date = datetime.now().date()
        
        # Save basic metrics
        if 'basic_metrics' in metrics:
            for metric_name, value in metrics['basic_metrics'].items():
                metric_records.append({
                    'portfolio_id': portfolio_id,
                    'equity_id': None,
                    'metric_date': calculation_date,
                    'metric_type': metric_name,
                    'value': value,
                    'period_days': 252
                })
        
        # Save VaR metrics
        if 'var_metrics' in metrics:
            for metric_name, value in metrics['var_metrics'].items():
                confidence_level = int(metric_name.split('_')[1]) / 100
                metric_records.append({
                    'portfolio_id': portfolio_id,
                    'equity_id': None,
                    'metric_date': calculation_date,
                    'metric_type': 'var',
                    'value': value,
                    'period_days': 252,
                    'confidence_level': confidence_level
                })
        
        # Save CVaR metrics
        if 'cvar_metrics' in metrics:
            for metric_name, value in metrics['cvar_metrics'].items():
                confidence_level = int(metric_name.split('_')[1]) / 100
                metric_records.append({
                    'portfolio_id': portfolio_id,
                    'equity_id': None,
                    'metric_date': calculation_date,
                    'metric_type': 'cvar',
                    'value': value,
                    'period_days': 252,
                    'confidence_level': confidence_level
                })
        
        # Save concentration metrics
        if 'concentration_metrics' in metrics:
            for metric_name, value in metrics['concentration_metrics'].items():
                metric_records.append({
                    'portfolio_id': portfolio_id,
                    'equity_id': None,
                    'metric_date': calculation_date,
                    'metric_type': f'concentration_{metric_name}',
                    'value': value,
                    'period_days': 252
                })
        
        return self.db.save_risk_metrics(metric_records)
    
    def get_risk_trend_analysis(self, portfolio_id: int, 
                               days_back: int = 90) -> pd.DataFrame:
        """Get trend analysis of risk metrics over time.
        
        Args:
            portfolio_id: Portfolio ID
            days_back: Number of days to look back
            
        Returns:
            DataFrame with risk metric trends
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        query = """
            SELECT 
                metric_date,
                metric_type,
                value,
                confidence_level
            FROM risk_metrics
            WHERE portfolio_id = %s
              AND metric_date >= %s
              AND metric_date <= %s
            ORDER BY metric_date DESC, metric_type
        """
        
        return self.db.get_dataframe(query, (portfolio_id, start_date, end_date))
