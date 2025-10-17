# 💼 Financial Portfolio Tracker

Professional portfolio management system with real-time market data integration and advanced analytics.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![SQLite](https://img.shields.io/badge/Database-SQLite-green.svg)](https://sqlite.org)
[![Power BI](https://img.shields.io/badge/Analytics-Power%20BI-yellow.svg)](https://powerbi.microsoft.com)
[![License](https://img.shields.io/badge/License-MIT-red.svg)](LICENSE)

## 🚀 Features

- **Real-time Market Data**: Live price feeds from Yahoo Finance API
- **Portfolio Management**: Track multiple portfolios with detailed position analysis
- **P&L Analytics**: Real-time profit/loss calculations with unrealized gains
- **SQL Analytics Engine**: Advanced views for portfolio performance analysis
- **Power BI Integration**: Ready-to-use data connections and dashboard templates
- **Professional Reporting**: Comprehensive portfolio summaries and performance metrics
- **Export Capabilities**: CSV exports for external analysis and reporting
- **Risk Analytics**: Beta analysis, concentration risk, and diversification metrics

## 📊 Live Demo Results

```
💼 PORTFOLIO PERFORMANCE SUMMARY
--------------------------------------------------
         Portfolio  Positions Cost_Basis Market_Value Unrealized_PL Total_Return
Conservative Income          5      $67,000      $94,990        $27,990        41.8%
   Growth Portfolio          5     $311,100     $169,656     -$141,444       -45.5%

📈 TOP HOLDINGS WITH LIVE PRICES
--------------------------------------------------
Symbol               Company Live_Price Market_Value Total_Return
  META   Meta Platforms Inc.    $717.55      $50,228        298.6%
   JPM  JPMorgan Chase & Co.    $305.69      $45,853        118.4%
  MSFT Microsoft Corporation    $513.43      $38,507         71.1%
   JNJ     Johnson & Johnson    $191.17      $38,233         19.5%
  TSLA            Tesla Inc.    $435.15      $34,811        117.6%
```

*Results from live Yahoo Finance API data as of October 2025*

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
│   └── README_PowerBI.md           # Power BI setup guide
├── exports/                        # CSV exports for external analysis
└── README.md                       # This documentation
```

## 🛠️ Quick Setup

### Prerequisites
- Python 3.8+
- SQLite3 (included with Python)
- Internet connection for live market data
- Power BI Desktop (optional, for dashboards)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/AnnieMahajan454/Financial-Portfolio-Tracker.git
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

   This will:
   - ✅ Create the SQLite database with full schema
   - ✅ Generate sample portfolios with realistic data
   - ✅ Fetch live market prices from Yahoo Finance
   - ✅ Display comprehensive performance analytics
   - ✅ Export data to CSV files

## 📋 Database Schema

### Core Tables
- **portfolios**: Portfolio definitions and metadata
- **securities**: Security master data with company information  
- **positions**: Current portfolio positions with cost basis
- **transactions**: Complete transaction history with timestamps
- **market_data**: Real-time and historical price data
- **portfolio_performance**: Daily performance snapshots

### Analytics Views
- **portfolio_summary**: Consolidated portfolio performance metrics
- **top_holdings**: Ranked holdings by market value
- **winners_losers**: Performance-categorized positions
- **sector_allocation**: Sector-wise portfolio breakdown
- **risk_metrics**: Risk analysis and diversification metrics

## 🔧 Usage Examples

### Basic Portfolio Operations

```python
from portfolio_tracker import PortfolioTracker

# Initialize tracker
tracker = PortfolioTracker('portfolio.db')

# Create a new portfolio
tracker.create_portfolio(
    name='Tech Growth',
    description='High-growth technology stocks',
    investment_style='Growth',
    risk_tolerance='High'
)

# Add transactions
tracker.add_transaction('Tech Growth', 'AAPL', 100, 150.00, 'BUY')
tracker.add_transaction('Tech Growth', 'GOOGL', 50, 2500.00, 'BUY')

# Update with live market data
live_prices = tracker.update_market_data()
print(f"Updated {len(live_prices)} securities with live prices")

# Generate comprehensive analysis
summary = tracker.get_portfolio_summary()
analytics = tracker.get_performance_analytics('Tech Growth')
```

### Real-time Market Data Integration

```python
from market_data_service import MarketDataService

# Initialize market data service
service = MarketDataService()

# Get live prices for multiple symbols
symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'META']
live_prices = service.get_live_prices(symbols)

for symbol, price in live_prices.items():
    print(f"{symbol}: ${price:.2f}")

# Get comprehensive company information
company_info = service.get_company_info('AAPL')
print(f"Market Cap: ${company_info['market_cap']:,}")
print(f"P/E Ratio: {company_info['pe_ratio']:.2f}")
```

### Advanced Analytics

```python
# Portfolio performance analysis
analytics = tracker.get_performance_analytics('Growth Portfolio')

print(f"Total Return: {analytics['total_return_percent']:.1f}%")
print(f"Portfolio Volatility: {analytics['portfolio_volatility']:.2f}%")
print(f"Largest Position: {analytics['largest_position']}")
print(f"Number of Positions: {analytics['number_of_positions']}")

# Export detailed reports
tracker.export_portfolio_data('Growth Portfolio', 'exports/')
```

## 📊 Power BI Integration

### Quick Setup
1. Open Power BI Desktop
2. Load `powerbi/datasource_config.pq`
3. Update database path in the configuration
4. Create stunning dashboards with pre-built analytics views

### Available Dashboards
- **Portfolio Performance Overview**: KPIs, trends, comparisons
- **Holdings Analysis**: Top positions, sector allocation
- **Risk Management**: Beta analysis, concentration metrics
- **Transaction Analysis**: Buy/sell activity, cash flow

See `powerbi/README_PowerBI.md` for detailed setup instructions.

## 🔍 Analytics Features

### Performance Metrics
- **Total Return %**: Comprehensive return calculations
- **Unrealized P&L**: Real-time profit/loss tracking
- **Cost Basis vs Market Value**: Position-level analysis
- **Daily Performance Attribution**: Track daily changes

### Risk Analysis
- **Portfolio Beta**: Systematic risk measurement
- **Concentration Risk**: Single-position exposure analysis
- **Sector Diversification**: Industry allocation tracking
- **Volatility Analysis**: Return standard deviation

### Market Data
- **Real-time Prices**: Live Yahoo Finance integration
- **Historical Data**: Multi-period performance analysis
- **Company Fundamentals**: P/E ratios, market cap, sector info
- **Volume Analysis**: Trading activity metrics

## 📈 Export Capabilities

All data can be exported to CSV format:
- Portfolio performance summaries
- Detailed position reports
- Complete transaction history
- Market data snapshots
- Risk analytics reports

```python
# Export all portfolio data
tracker.export_portfolio_data('Portfolio Name', 'exports/')

# Files created:
# - Portfolio_Name_positions_20241016_143022.csv
# - Portfolio_Name_transactions_20241016_143022.csv  
# - Portfolio_Name_summary_20241016_143022.csv
```

## 🚨 System Requirements

- **Memory**: Minimum 4GB RAM (8GB recommended for large portfolios)
- **Storage**: 1GB available space for database and exports
- **Network**: Internet connection required for live market data
- **Python**: Version 3.8 or higher
- **Database**: SQLite3 (included with Python installation)

## 🔐 Security & Privacy

- **Local Storage**: All data stored locally in SQLite database
- **Read-only APIs**: Market data accessed via read-only Yahoo Finance API
- **No Account Integration**: No sensitive financial account connections
- **Privacy-focused**: No data transmitted to external services
- **Audit Trail**: Complete transaction history with timestamps

## 🛠️ Advanced Configuration

### Custom Market Data Sources
Extend the `MarketDataService` class to integrate additional data providers:

```python
class CustomMarketDataService(MarketDataService):
    def get_live_prices_custom_source(self, symbols):
        # Implement custom data source integration
        pass
```

### Custom Analytics Views
Add specialized SQL views in `sql/03_analytics_views.sql`:

```sql
CREATE VIEW custom_analysis AS
SELECT 
    portfolio_name,
    symbol,
    -- Your custom calculations here
FROM positions p
JOIN portfolios port ON p.portfolio_id = port.portfolio_id;
```

### Performance Optimization
- **Database Indexing**: Add indexes for frequently queried columns
- **Batch Processing**: Process large transaction sets in batches
- **Caching**: Implement caching for frequently accessed market data
- **Connection Pooling**: Use connection pooling for high-volume operations

## 🧪 Testing

Run the comprehensive demo to verify installation:

```bash
python python/demo_database_setup.py
```

Expected output:
- ✅ Database schema created
- ✅ Sample data inserted
- ✅ Live market data retrieved
- ✅ Analytics calculations completed
- ✅ Data exported successfully

## 🔄 Data Updates

### Manual Updates
```bash
# Run the demo script to refresh all data
python python/demo_database_setup.py

# Update only market data
python -c "from portfolio_tracker import PortfolioTracker; PortfolioTracker().update_market_data()"
```

### Automated Updates
Set up scheduled tasks (cron/Task Scheduler) to run market data updates:

```bash
# Daily market data update at 9:30 AM
30 9 * * 1-5 cd /path/to/project && python python/demo_database_setup.py
```

## 📚 Documentation

- **Main README**: Complete system overview (this file)
- **Power BI Guide**: `powerbi/README_PowerBI.md`
- **SQL Schema**: Detailed comments in `sql/*.sql` files
- **API Documentation**: Docstrings in Python source files

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Yahoo Finance API**: Real-time market data
- **SQLite**: Lightweight, serverless database
- **Pandas**: Data manipulation and analysis
- **Power BI**: Professional analytics and visualization
- **Python Community**: Excellent libraries and documentation

## 📞 Support

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Documentation**: Check inline code comments and SQL schema
- **Community**: Discussions welcome in GitHub Discussions

---

## 🎯 Professional Portfolio Management Made Simple

**Transform your investment tracking with institutional-grade analytics and real-time market data integration.**

### Key Differentiators:
✨ **Enterprise-Ready**: Professional database design with full audit trails  
📊 **Real-Time Analytics**: Live market data integration with Yahoo Finance API  
🔧 **Power BI Integration**: Production-ready business intelligence dashboards  
📈 **Advanced Metrics**: Risk analytics, sector allocation, performance attribution  
🚀 **Easy Setup**: One-command demo with sample data and live results  

*Built for investors, analysts, and portfolio managers who demand professional-grade tools.*