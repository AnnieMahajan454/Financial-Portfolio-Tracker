# 📊 Financial Portfolio Tracker

A comprehensive portfolio management system that provides real-time portfolio tracking, performance analytics, and interactive dashboards.

## 🚀 Features

- **Real-time Market Data**: Live price feeds from Yahoo Finance API
- **Portfolio Performance**: Track P&L, returns, and allocation
- **Risk Analytics**: Sector diversification and exposure analysis  
- **Interactive Dashboards**: Power BI visualizations and reporting
- **Multi-database Support**: PostgreSQL and SQLite compatibility

## 📁 Project Structure

```
├── sql/                    # Database schema and queries
├── python/                 # Python scripts and demo
├── powerbi/               # Power BI dashboard templates
└── docs/                  # Documentation and guides
```

## 🛠️ Quick Start

### Prerequisites
- Python 3.8+ 
- SQLite or PostgreSQL
- Power BI Desktop (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Financial-Portfolio-Tracker
   ```

2. **Run the demo**
   ```bash
   python python/demo_database_setup.py
   ```

3. **View results**
   - SQLite database: `portfolio_tracker_demo.db`
   - CSV exports: `data/` folder
   - Import CSV files into Power BI for dashboards

## 📊 Demo Results

The demo creates live portfolios with real market data:
- **Conservative Income Portfolio**: 3 positions, 41.78% return
- **Growth Portfolio**: 6 positions tracking tech stocks
- **Real-time pricing** from Yahoo Finance
- **Performance analytics** and sector allocation
- **Risk analysis** and diversification metrics

## 💡 Use Cases

- Personal portfolio tracking
- Investment performance analysis
- Risk management and diversification
- Financial reporting and dashboards
- Educational finance projects

## 🔧 Technical Stack

- **Database**: PostgreSQL/SQLite
- **Backend**: Python with pandas, yfinance
- **Analytics**: SQL views and Python calculations
- **Visualization**: Power BI, CSV exports
- **API**: Yahoo Finance for market data

## 📖 Documentation

See the `docs/` folder for detailed setup guides and configuration instructions.

## 🤝 Contributing

Contributions welcome! Please read the contributing guidelines before submitting PRs.

## 📄 License

MIT License - see LICENSE file for details.