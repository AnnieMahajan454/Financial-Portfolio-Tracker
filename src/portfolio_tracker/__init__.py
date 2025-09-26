"""
Financial Portfolio Tracker

A Python library for tracking and analyzing financial portfolios with 
automated risk exposure analysis and Power BI integration.
"""

__version__ = "1.0.0"
__author__ = "Annie Mahajan"

from .database import DatabaseManager
from .portfolio import PortfolioManager
from .data_fetcher import DataFetcher
from .risk_analyzer import RiskAnalyzer
from .powerbi_exporter import PowerBIExporter

__all__ = [
    'DatabaseManager',
    'PortfolioManager', 
    'DataFetcher',
    'RiskAnalyzer',
    'PowerBIExporter'
]
