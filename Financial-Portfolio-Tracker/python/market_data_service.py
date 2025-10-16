"""
Market Data Service
Real-time market data integration using Yahoo Finance API
"""

import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import requests

class MarketDataService:
    """
    Professional market data service with real-time price feeds
    and historical data management
    """
    
    def __init__(self, db_path: str = "portfolio.db", rate_limit: float = 0.1):
        """
        Initialize market data service
        
        Args:
            db_path: Path to SQLite database
            rate_limit: Seconds to wait between API calls
        """
        self.db_path = db_path
        self.rate_limit = rate_limit
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def get_live_prices(self, symbols: List[str]) -> Dict[str, float]:
        """
        Fetch live prices for given symbols
        
        Args:
            symbols: List of stock symbols (e.g., ['AAPL', 'GOOGL'])
            
        Returns:
            Dictionary mapping symbol to current price
        """
        prices = {}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                # Try to get current price from multiple sources
                current_price = (
                    info.get('currentPrice') or 
                    info.get('regularMarketPrice') or
                    info.get('previousClose')
                )
                
                if current_price:
                    prices[symbol] = float(current_price)
                    self.logger.info(f"Retrieved price for {symbol}: ${current_price:.2f}")
                else:
                    # Fallback to history data
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        prices[symbol] = float(hist['Close'].iloc[-1])
                        self.logger.info(f"Retrieved historical price for {symbol}: ${prices[symbol]:.2f}")
                    else:
                        self.logger.warning(f"Could not retrieve price for {symbol}")
                
                time.sleep(self.rate_limit)
                
            except Exception as e:
                self.logger.error(f"Error fetching price for {symbol}: {e}")
                continue
                
        return prices
    
    def get_company_info(self, symbol: str) -> Dict:
        """
        Get comprehensive company information
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Company information dictionary
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'company_name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                '52_week_high': info.get('fiftyTwoWeekHigh', 0),
                '52_week_low': info.get('fiftyTwoWeekLow', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching company info for {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def get_historical_data(self, symbols: List[str], period: str = "1y") -> pd.DataFrame:
        """
        Get historical price data
        
        Args:
            symbols: List of stock symbols
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            
        Returns:
            DataFrame with historical data
        """
        all_data = []
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                
                if not hist.empty:
                    hist['Symbol'] = symbol
                    hist.reset_index(inplace=True)
                    all_data.append(hist)
                    
                time.sleep(self.rate_limit)
                
            except Exception as e:
                self.logger.error(f"Error fetching historical data for {symbol}: {e}")
                continue
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        else:
            return pd.DataFrame()
    
    def store_market_data(self, symbol: str, price: float) -> bool:
        """
        Store market data in database
        
        Args:
            symbol: Stock symbol
            price: Current price
            
        Returns:
            Success status
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert or update market data
            cursor.execute("""
                INSERT OR REPLACE INTO market_data 
                (symbol, price, timestamp, source)
                VALUES (?, ?, ?, ?)
            """, (symbol, price, datetime.now(), 'yahoo_finance'))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing market data: {e}")
            return False
    
    def update_all_market_data(self, symbols: List[str]) -> Dict[str, float]:
        """
        Update market data for all symbols and store in database
        
        Args:
            symbols: List of stock symbols to update
            
        Returns:
            Dictionary of updated prices
        """
        self.logger.info(f"Updating market data for {len(symbols)} symbols")
        
        prices = self.get_live_prices(symbols)
        
        # Store in database
        for symbol, price in prices.items():
            self.store_market_data(symbol, price)
        
        self.logger.info(f"Updated {len(prices)} prices successfully")
        return prices
    
    def get_market_summary(self, symbols: List[str]) -> pd.DataFrame:
        """
        Get comprehensive market summary
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            DataFrame with market summary data
        """
        summary_data = []
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period="1d")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    
                    summary_data.append({
                        'Symbol': symbol,
                        'Company': info.get('longName', '')[:30],
                        'Price': current_price,
                        'Volume': hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0,
                        'Market Cap': info.get('marketCap', 0),
                        'P/E Ratio': info.get('trailingPE', 0),
                        'Sector': info.get('sector', ''),
                        '52W High': info.get('fiftyTwoWeekHigh', 0),
                        '52W Low': info.get('fiftyTwoWeekLow', 0)
                    })
                
                time.sleep(self.rate_limit)
                
            except Exception as e:
                self.logger.error(f"Error in market summary for {symbol}: {e}")
                continue
        
        return pd.DataFrame(summary_data)
    
    def calculate_returns(self, symbol: str, period: str = "1y") -> Dict[str, float]:
        """
        Calculate various return metrics
        
        Args:
            symbol: Stock symbol
            period: Time period for calculation
            
        Returns:
            Dictionary of return metrics
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if len(hist) < 2:
                return {}
            
            returns = hist['Close'].pct_change().dropna()
            
            return {
                'total_return': ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100,
                'annualized_return': returns.mean() * 252 * 100,
                'volatility': returns.std() * np.sqrt(252) * 100,
                'sharpe_ratio': (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0,
                'max_drawdown': ((hist['Close'] / hist['Close'].expanding().max()) - 1).min() * 100
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating returns for {symbol}: {e}")
            return {}


if __name__ == "__main__":
    # Demo usage
    service = MarketDataService()
    
    # Test symbols
    test_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'META']
    
    # Get live prices
    print("📈 LIVE MARKET PRICES")
    print("-" * 50)
    prices = service.get_live_prices(test_symbols)
    for symbol, price in prices.items():
        print(f"{symbol:>6}: ${price:>8.2f}")
    
    # Get market summary
    print("\n📊 MARKET SUMMARY")
    print("-" * 50)
    summary = service.get_market_summary(test_symbols[:3])
    print(summary.to_string(index=False))