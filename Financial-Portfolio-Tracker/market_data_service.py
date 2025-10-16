"""
Market Data Service - Yahoo Finance API Integration
Provides real-time and historical market data for portfolio tracking
"""

import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketDataService:
    """Service for fetching real-time and historical market data"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        
    def get_live_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Fetch current market prices for given symbols
        
        Args:
            symbols: List of stock symbols (e.g., ['AAPL', 'GOOGL'])
            
        Returns:
            Dictionary mapping symbols to current prices
        """
        prices = {}
        
        try:
            # Create tickers object for batch processing
            tickers = yf.Tickers(' '.join(symbols))
            
            for symbol in symbols:
                try:
                    ticker = tickers.tickers[symbol]
                    info = ticker.info
                    
                    # Try multiple price fields in order of preference
                    current_price = (
                        info.get('currentPrice') or 
                        info.get('regularMarketPrice') or 
                        info.get('previousClose') or
                        info.get('bid') or
                        info.get('ask')
                    )
                    
                    if current_price and current_price > 0:
                        prices[symbol] = float(current_price)
                        logger.info(f"Fetched price for {symbol}: ${current_price:.2f}")
                    else:
                        logger.warning(f"No valid price found for {symbol}")
                        
                except Exception as e:
                    logger.error(f"Error fetching price for {symbol}: {e}")
                    
                # Rate limiting
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in batch price fetch: {e}")
            
        return prices
    
    def get_security_info(self, symbol: str) -> Dict[str, str]:
        """
        Get detailed information about a security
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with security information
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'company_name': info.get('longName', 'N/A'),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'currency': info.get('currency', 'USD'),
                'exchange': info.get('exchange', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'description': info.get('longBusinessSummary', 'N/A')[:500]  # Truncate
            }
            
        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {e}")
            return {
                'symbol': symbol,
                'company_name': 'N/A',
                'sector': 'N/A', 
                'industry': 'N/A',
                'currency': 'USD',
                'exchange': 'N/A',
                'market_cap': 0,
                'description': 'N/A'
            }
    
    def get_historical_prices(self, symbol: str, period: str = "1mo") -> pd.DataFrame:
        """
        Get historical price data for a symbol
        
        Args:
            symbol: Stock symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            DataFrame with historical price data
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if not hist.empty:
                hist['Symbol'] = symbol
                hist.reset_index(inplace=True)
                return hist
            else:
                logger.warning(f"No historical data found for {symbol}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def validate_symbols(self, symbols: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate that symbols exist and are tradeable
        
        Args:
            symbols: List of symbols to validate
            
        Returns:
            Tuple of (valid_symbols, invalid_symbols)
        """
        valid = []
        invalid = []
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                # Check if we can get basic info
                if info.get('symbol') or info.get('longName'):
                    valid.append(symbol)
                    logger.info(f"✓ {symbol} is valid")
                else:
                    invalid.append(symbol)
                    logger.warning(f"✗ {symbol} is invalid")
                    
            except Exception as e:
                invalid.append(symbol)
                logger.error(f"✗ {symbol} validation failed: {e}")
                
            time.sleep(0.1)  # Rate limiting
            
        return valid, invalid
    
    def get_market_status(self) -> Dict[str, str]:
        """
        Get current market status information
        
        Returns:
            Dictionary with market status info
        """
        try:
            # Use SPY as proxy for market status
            spy = yf.Ticker("SPY")
            info = spy.info
            
            return {
                'market_state': info.get('marketState', 'UNKNOWN'),
                'timezone': info.get('timeZoneFullName', 'America/New_York'),
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'currency': 'USD'
            }
            
        except Exception as e:
            logger.error(f"Error getting market status: {e}")
            return {
                'market_state': 'UNKNOWN',
                'timezone': 'America/New_York', 
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'currency': 'USD'
            }

def main():
    """Demo of market data service functionality"""
    print("🔥 Market Data Service Demo")
    print("=" * 50)
    
    service = MarketDataService()
    
    # Test symbols
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
    
    print("\n📊 Live Market Prices")
    print("-" * 30)
    prices = service.get_live_prices(symbols)
    
    for symbol, price in prices.items():
        print(f"{symbol:>6}: ${price:>8.2f}")
    
    print("\n🏢 Company Information")
    print("-" * 30)
    info = service.get_security_info('AAPL')
    print(f"Company: {info['company_name']}")
    print(f"Sector: {info['sector']}")
    print(f"Industry: {info['industry']}")
    
    print("\n✅ Symbol Validation")
    print("-" * 30)
    test_symbols = ['AAPL', 'INVALID123', 'GOOGL', 'FAKESTK']
    valid, invalid = service.validate_symbols(test_symbols)
    print(f"Valid: {valid}")
    print(f"Invalid: {invalid}")
    
    print("\n🕒 Market Status")
    print("-" * 30)
    status = service.get_market_status()
    for key, value in status.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()