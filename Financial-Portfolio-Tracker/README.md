# 💼 Financial Portfolio Tracker

Professional portfolio management system with real-time market data integration and advanced analytics.

## 🚀 Features

- **Real-time Market Data**: Live price feeds from Yahoo Finance API
- **Portfolio Management**: Track multiple portfolios with detailed position analysis
- **P&L Analytics**: Real-time profit/loss calculations with unrealized gains
- **SQL Analytics Engine**: Advanced views for portfolio performance analysis
- **Power BI Integration**: Ready-to-use data connections and dashboard templates
- **Professional Reporting**: Comprehensive portfolio summaries and performance metrics

## 📊 Live Demo Results

```
💼 PORTFOLIO PERFORMANCE SUMMARY
--------------------------------------------------
         Portfolio  Positions Cost_Basis Market_Value Unrealized_PL Total_Return
Conservative Income          3      $67,000      $94,990        $27,990        41.8%
   Growth Portfolio          6     $311,100     $169,656     -$141,444       -45.5%

📈 TOP HOLDINGS WITH LIVE PRICES
--------------------------------------------------
Symbol               Company Live_Price Market_Value Total_Return
  META   Meta Platforms Inc.    $717.55      $50,228        298.6%
   JPM  JPMorgan Chase & Co.    $305.69      $45,853        118.4%
  MSFT Microsoft Corporation    $513.43      $38,507         71.1%
   JNJ     Johnson & Johnson    $191.17      $38,233         19.5%
  TSLA            Tesla Inc.    $435.15      $34,811        117.6%
```

## 🏗️ System Architecture

```
Financial-Portfolio-Tracker/
├── python/                          # Core application and data processing
│   ├── demo_database_setup.py      # Complete system setup and demo
│   ├── portfolio_tracker.py        # Main portfolio management class
│   ├── market_data_service.py      # Yahoo Finance API integration
│   └── requirements.txt            # Python dependencies
├── sql/                            # Database schema and analytics
│   ├── 01_create_database_schema.sql   # Core database structure
│   ├── 02_sample_data.sql             # Demo portfolio data
│   └── 03_analytics_views.sql         # Advanced analytics views
├── powerbi/                        # Business Intelligence integration
│   ├── datasource_config.pq        # Power BI data connection
│   └── dashboard_template.pbix     # Pre-built dashboard template
├── exports/                        # CSV exports for external analysis
└── README.md                       # This documentation
```

## 🛠️ Quick Setup

### Prerequisites
- Python 3.8+
- SQLite3
- Power BI Desktop (optional)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Financial-Portfolio-Tracker
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r python/requirements.txt
   ```

3. **Run the complete demo**:
   ```bash
   python python/demo_database_setup.py
   ```

## 📋 Database Schema

### Core Tables
- **portfolios**: Portfolio definitions and metadata
- **securities**: Security master data with company information
- **positions**: Current portfolio positions
- **transactions**: Complete transaction history
- **market_data**: Historical and real-time price data
- **portfolio_performance**: Daily performance snapshots
- **alerts**: Price and performance alerts
- **user_preferences**: System configuration

### Analytics Views
- **portfolio_summary**: Consolidated portfolio performance
- **top_holdings**: Top positions by market value
- **winners_losers**: Best and worst performing securities
- **daily_pnl**: Daily profit and loss analysis

## 🔧 Usage Examples

### Basic Portfolio Tracking
```python
from portfolio_tracker import PortfolioTracker

# Initialize tracker
tracker = PortfolioTracker('portfolio.db')

# Create portfolio
tracker.create_portfolio('Growth Portfolio', 'High growth technology focus')

# Add positions
tracker.add_transaction('Growth Portfolio', 'AAPL', 100, 150.00, 'BUY')
tracker.add_transaction('Growth Portfolio', 'GOOGL', 50, 2500.00, 'BUY')

# Update with live prices
tracker.update_market_data()

# Generate reports
summary = tracker.get_portfolio_summary()
print(summary)
```

### Real-time Market Data
```python
from market_data_service import MarketDataService

# Get live prices
service = MarketDataService()
prices = service.get_live_prices(['AAPL', 'GOOGL', 'MSFT'])
print(f"AAPL: ${prices['AAPL']:.2f}")
```

## 📊 Power BI Integration

### Data Connection
1. Open Power BI Desktop
2. Import `powerbi/datasource_config.pq`
3. Configure database path in connection string
4. Load pre-built dashboard template

### Available Dashboards
- Portfolio Performance Overview
- Security Analysis Deep Dive
- P&L Trending and Attribution
- Risk Metrics and Diversification

## 🔍 Analytics Features

### Performance Metrics
- Total Return (%)
- Unrealized P&L
- Cost Basis vs Market Value
- Position Concentration
- Daily Performance Attribution

### Risk Analysis
- Portfolio Diversification
- Security Concentration Risk
- Volatility Analysis
- Drawdown Metrics

## 📈 Export Capabilities

All data can be exported to CSV for external analysis:
- Portfolio summaries
- Position details
- Transaction history
- Market data snapshots
- Performance analytics

## 🚨 System Requirements

- **Memory**: Minimum 4GB RAM
- **Storage**: 1GB for database and exports
- **Network**: Internet connection for live market data
- **Python**: Version 3.8 or higher
- **Database**: SQLite3 (included with Python)

## 🔐 Security & Compliance

- Local database storage (no cloud dependencies)
- Read-only market data API access
- No sensitive financial account integration
- Privacy-focused design
- Audit trail for all transactions

## 🛠️ Advanced Configuration

### Custom Market Data Sources
Extend `MarketDataService` class to integrate additional data providers.

### Custom Analytics
Add new SQL views in `sql/03_analytics_views.sql` for specialized analysis.

### Performance Optimization
- Database indexing for large portfolios
- Caching for frequently accessed data
- Batch processing for bulk operations

## 📞 Support

For technical support or feature requests, please create an issue in the repository.

## 📄 License

This project is released under the MIT License. See LICENSE file for details.

---

**🎯 Professional Portfolio Management Made Simple**

Track your investments with institutional-grade analytics and real-time market data integration.