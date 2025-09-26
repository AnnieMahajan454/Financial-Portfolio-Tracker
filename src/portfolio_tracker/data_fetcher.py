"""
Data Fetcher for Portfolio Tracker

Handles fetching real-time and historical equity data from various sources
including Alpha Vantage, Yahoo Finance, and other financial APIs.
"""

import time
import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed


class DataFetcher:
    """Fetches financial data from various sources."""
    
    def __init__(self, alpha_vantage_key: str = None, rate_limit: float = 0.2):
        """Initialize the data fetcher.
        
        Args:
            alpha_vantage_key: Alpha Vantage API key
            rate_limit: Minimum time between API calls (seconds)
        """
        self.alpha_vantage_key = alpha_vantage_key
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.logger = logging.getLogger(__name__)
        
    def _rate_limit_check(self):
        """Enforce rate limiting between API calls."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a single symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Current price or None if failed
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                return float(data['Close'].iloc[-1])
        except Exception as e:
            self.logger.error(f"Error fetching price for {symbol}: {e}")
        return None
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current prices for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbols to current prices
        """
        prices = {}
        
        # Use ThreadPoolExecutor for concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_symbol = {
                executor.submit(self.get_current_price, symbol): symbol 
                for symbol in symbols
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    price = future.result()
                    if price is not None:
                        prices[symbol] = price
                except Exception as e:
                    self.logger.error(f"Error fetching price for {symbol}: {e}")
        
        return prices
    
    def get_historical_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Get historical price data for a symbol.
        
        Args:
            symbol: Stock symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            DataFrame with historical price data
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if not data.empty:
                # Reset index to make Date a column
                data = data.reset_index()
                data['Symbol'] = symbol
                return data
                
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {e}")
        
        return pd.DataFrame()
    
    def get_bulk_historical_data(self, symbols: List[str], 
                                period: str = "1y") -> pd.DataFrame:
        """Get historical data for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            period: Time period
            
        Returns:
            Combined DataFrame with historical data for all symbols
        """
        all_data = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_symbol = {
                executor.submit(self.get_historical_data, symbol, period): symbol 
                for symbol in symbols
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    data = future.result()
                    if not data.empty:
                        all_data.append(data)
                except Exception as e:
                    self.logger.error(f"Error fetching historical data for {symbol}: {e}")
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()
    
    def get_company_info(self, symbol: str) -> Dict:
        """Get company information for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with company information
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'company_name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'exchange': info.get('exchange', ''),
                'currency': info.get('currency', 'USD'),
                'market_cap': info.get('marketCap', 0),
                'beta': info.get('beta', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'book_value': info.get('bookValue', 0),
                'price_to_book': info.get('priceToBook', 0),
                'enterprise_value': info.get('enterpriseValue', 0),
                'profit_margins': info.get('profitMargins', 0),
                'operating_margins': info.get('operatingMargins', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching company info for {symbol}: {e}")
            return {'symbol': symbol, 'company_name': f'Company for {symbol}'}
    
    def get_bulk_company_info(self, symbols: List[str]) -> List[Dict]:
        """Get company information for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            List of dictionaries with company information
        """
        company_info = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_symbol = {
                executor.submit(self.get_company_info, symbol): symbol 
                for symbol in symbols
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    info = future.result()
                    company_info.append(info)
                except Exception as e:
                    self.logger.error(f"Error fetching company info for {symbol}: {e}")
        
        return company_info
    
    def get_intraday_data(self, symbol: str, interval: str = "5min") -> pd.DataFrame:
        """Get intraday price data using Alpha Vantage.
        
        Args:
            symbol: Stock symbol
            interval: Time interval (1min, 5min, 15min, 30min, 60min)
            
        Returns:
            DataFrame with intraday data
        """
        if not self.alpha_vantage_key:
            self.logger.warning("Alpha Vantage API key not provided")
            return pd.DataFrame()
        
        self._rate_limit_check()
        
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "apikey": self.alpha_vantage_key,
            "outputsize": "compact"
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if f"Time Series ({interval})" in data:
                time_series = data[f"Time Series ({interval})"]
                
                df = pd.DataFrame.from_dict(time_series, orient='index')
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                
                # Rename columns
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                df = df.astype(float)
                df['Symbol'] = symbol
                df = df.reset_index().rename(columns={'index': 'Datetime'})
                
                return df
                
        except Exception as e:
            self.logger.error(f"Error fetching intraday data for {symbol}: {e}")
        
        return pd.DataFrame()
    
    def get_market_news(self, symbols: List[str] = None, limit: int = 10) -> List[Dict]:
        """Get market news for symbols or general market news.
        
        Args:
            symbols: List of symbols to get news for (optional)
            limit: Maximum number of news items to return
            
        Returns:
            List of news items
        """
        # This is a placeholder implementation
        # In practice, you would integrate with news APIs like NewsAPI, 
        # Alpha Vantage News, or financial news providers
        
        news_items = []
        
        if symbols:
            for symbol in symbols[:limit]:
                news_items.append({
                    'symbol': symbol,
                    'title': f'Market Update for {symbol}',
                    'summary': f'Latest market analysis and news for {symbol}',
                    'source': 'Market News API',
                    'published_at': datetime.now().isoformat(),
                    'url': f'https://example.com/news/{symbol}'
                })
        else:
            # General market news
            for i in range(limit):
                news_items.append({
                    'title': f'Market Update {i+1}',
                    'summary': 'General market news and analysis',
                    'source': 'Market News API',
                    'published_at': datetime.now().isoformat(),
                    'url': f'https://example.com/news/{i+1}'
                })
        
        return news_items
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol exists and is tradeable.
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            True if symbol is valid, False otherwise
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return 'longName' in info and info.get('longName') is not None
        except:
            return False
    
    def get_sector_performance(self) -> pd.DataFrame:
        """Get sector performance data.
        
        Returns:
            DataFrame with sector performance metrics
        """
        # Major sector ETFs for tracking sector performance
        sector_etfs = {
            'XLE': 'Energy',
            'XLF': 'Financials', 
            'XLV': 'Health Care',
            'XLI': 'Industrials',
            'XLK': 'Technology',
            'XLP': 'Consumer Staples',
            'XLY': 'Consumer Discretionary',
            'XLU': 'Utilities',
            'XLB': 'Materials',
            'XLRE': 'Real Estate',
            'XLC': 'Communication Services'
        }
        
        sector_data = []
        
        for etf, sector in sector_etfs.items():
            try:
                ticker = yf.Ticker(etf)
                hist = ticker.history(period="5d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                    daily_change = ((current_price - prev_price) / prev_price) * 100
                    
                    sector_data.append({
                        'sector': sector,
                        'etf_symbol': etf,
                        'current_price': current_price,
                        'daily_change_pct': daily_change
                    })
                    
            except Exception as e:
                self.logger.error(f"Error fetching sector data for {etf}: {e}")
        
        return pd.DataFrame(sector_data)
