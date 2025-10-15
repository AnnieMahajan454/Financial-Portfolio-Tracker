# Financial Portfolio Tracker

A comprehensive, enterprise-grade portfolio management system built with SQL, Power BI, and minimal Python.

## Overview

Professional-grade investment portfolio tracking system that provides real-time portfolio analysis, advanced risk analytics, and stunning Power BI visualizations. Built primarily with SQL and Power BI, with minimal Python for data ingestion.

## Key Features

- **Real-time Portfolio Tracking**: Track 200+ equities with live price updates
- **Advanced Risk Analytics**: VaR, CVaR, Beta, Sharpe ratio, and comprehensive risk metrics
- **Professional Power BI Dashboards**: Multiple comprehensive dashboard pages with advanced visualizations
- **Automated Data Pipeline**: One-click automation for data fetching and processing
- **Institutional-Grade Analytics**: Performance attribution, sector analysis, and benchmark comparison
- **Comprehensive Risk Management**: Diversification analysis, concentration risk, and stress testing

## Architecture

### Database Layer (PostgreSQL)
- 15+ tables with proper relationships and constraints
- Advanced analytics views with complex calculations
- Optimized indexes for query performance
- Sample data including major securities and portfolios

### Python Layer
- Real-time data fetcher using Yahoo Finance API
- Portfolio analytics engine with risk calculations
- CSV export functionality for Power BI integration
- Minimal dependencies (yfinance, pandas, psycopg2)

### Power BI Layer
- Professional dashboard configuration
- Data source connections and transformations
- Advanced visualizations and interactive features

## Quick Start

1. **Setup Database**: Run `setup_database.bat`
2. **Configure**: Update `python/database_config.json` with your PostgreSQL password
3. **Run System**: Execute `run_portfolio_tracker.bat`
4. **Open Power BI**: Connect to generated CSV files in `data/` folder

## System Requirements

- PostgreSQL 12 or higher
- Python 3.8 or higher
- Power BI Desktop (latest version)
- Windows (batch scripts optimized for Windows)

## Project Structure

```
Financial-Portfolio-Tracker/
├── sql/                    # Database schema and scripts
├── python/                 # Data processing scripts
├── powerbi/               # Power BI configuration
├── data/                  # Data export directory
└── docs/                  # Documentation
```
