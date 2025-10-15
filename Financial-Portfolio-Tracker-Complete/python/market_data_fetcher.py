"""
Financial Portfolio Tracker - Market Data Fetcher
Core functionality for fetching real-time and historical market data
"""

import yfinance as yf
import pandas as pd
import psycopg2
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('market_data_fetcher.log'),
        logging.StreamHandler()
    ]
)

class DatabaseConnection:
    """Handles database connections and operations"""
    
    def __init__(self, config_file: str = 'database_config.json'):
        self.config = self.load_config(config_file)
        self.connection = None
        
    def load_config(self, config_file: str) -> dict:
        """Load database configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default configuration
            return {
                "host": "localhost",
                "port": 5432,
                "database": "portfolio_tracker",
                "user": "postgres",
                "password": "your_password"
            }
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(**self.config)
            logging.info("Database connection established")
        except Exception as e:
            logging.error(f"Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logging.info("Database connection closed")