# Power BI Integration Guide

## 📊 Dashboard Templates

This directory contains Power BI integration files for the Financial Portfolio Tracker. The system provides ready-to-use data connections and dashboard templates for comprehensive portfolio analytics.

## 🚀 Quick Setup

### Prerequisites
- Power BI Desktop (latest version)
- SQLite ODBC Driver installed
- Portfolio database (`portfolio.db`) generated from the Python application

### Connection Steps

1. **Open Power BI Desktop**

2. **Import Data Source Configuration**
   - Copy the contents of `datasource_config.pq`
   - In Power BI, go to Home → Transform Data → Advanced Editor
   - Paste the M query code
   - Update the `DatabasePath` variable to point to your `portfolio.db` file

3. **Load Data**
   - Click "Close & Apply" to load all tables and views
   - The system will automatically create relationships between tables

## 📈 Available Dashboard Templates

### 1. Portfolio Performance Overview
- **Metrics**: Total return, P&L, portfolio value trends
- **Visuals**: KPI cards, line charts, portfolio comparison
- **Filters**: Time period, portfolio selection

### 2. Holdings Analysis
- **Metrics**: Top holdings, sector allocation, position sizing
- **Visuals**: Treemap, donut charts, detailed tables
- **Filters**: Portfolio, sector, holding size

### 3. Risk Management Dashboard
- **Metrics**: Beta analysis, concentration risk, diversification
- **Visuals**: Risk scorecards, scatter plots, heat maps
- **Filters**: Risk tolerance, portfolio type

### 4. Transaction Analysis
- **Metrics**: Buy/sell activity, cash flow analysis
- **Visuals**: Transaction timeline, volume analysis
- **Filters**: Date range, transaction type, symbol

## 🔧 Data Model

### Core Tables
- **Portfolios**: Portfolio metadata and settings
- **Positions**: Current holdings with calculated metrics
- **Securities**: Company information and market data
- **Transactions**: Complete transaction history
- **Market Data**: Real-time price feeds

### Analytics Views
- **portfolio_summary**: Consolidated portfolio performance
- **top_holdings**: Ranked holdings by market value
- **winners_losers**: Performance categorized positions
- **sector_allocation**: Sector-wise portfolio breakdown
- **risk_metrics**: Risk analysis metrics

## 📊 Key Performance Indicators (KPIs)

### Portfolio Level
```
Total Return % = (Market Value - Cost Basis) / Cost Basis * 100
Unrealized P&L = Market Value - Cost Basis
Portfolio Value = Sum of (Quantity × Current Price)
Number of Positions = Count of unique symbols
```

### Position Level
```
Position Return % = (Current Price - Average Cost) / Average Cost * 100
Market Value = Quantity × Current Price
Unrealized P&L = Market Value - Cost Basis
Weight % = Position Market Value / Total Portfolio Value * 100
```

### Risk Metrics
```
Portfolio Beta = Weighted Average of Individual Stock Betas
Concentration Risk = Largest Position / Total Portfolio Value * 100
Sector Diversification = Count of Distinct Sectors
```

## 🎨 Dashboard Design Guidelines

### Color Scheme
- **Positive Returns**: Green (#008000)
- **Negative Returns**: Red (#FF0000)
- **Neutral/Info**: Blue (#0066CC)
- **Warning**: Orange (#FF8C00)

### Visual Standards
- Use consistent formatting for currency values
- Apply conditional formatting for performance metrics
- Include drill-through capabilities for detailed analysis
- Ensure responsive design for different screen sizes

## 🔄 Data Refresh

### Manual Refresh
1. Run the Python demo script to update market data
2. In Power BI, click "Refresh" to pull latest data
3. Verify timestamp on market data table

### Scheduled Refresh (Power BI Service)
1. Publish the report to Power BI Service
2. Configure data gateway for SQLite connection
3. Set up scheduled refresh (daily recommended for market data)

## 📱 Mobile Optimization

The dashboard templates are optimized for mobile viewing:
- Key metrics displayed in mobile-friendly layouts
- Touch-optimized filters and navigation
- Condensed visuals for smaller screens

## 🛠️ Customization Options

### Adding New Visuals
1. Use the comprehensive_data table for most visualizations
2. Leverage the pre-built analytics views for complex metrics
3. Add custom DAX measures for specific calculations

### Custom Measures (DAX Examples)
```dax
// Portfolio Sharpe Ratio
Sharpe Ratio = 
DIVIDE(
    AVERAGE(comprehensive_data[return_percent]) - 3, // Assuming 3% risk-free rate
    STDEV.P(comprehensive_data[return_percent])
)

// Sector Concentration
Max Sector Weight = 
MAXX(
    VALUES(comprehensive_data[sector]),
    CALCULATE(
        DIVIDE(
            SUM(comprehensive_data[market_value]),
            CALCULATE(SUM(comprehensive_data[market_value]), ALL(comprehensive_data[sector]))
        )
    )
)
```

## 🔗 Integration with Other Tools

### Excel Integration
- Export data to Excel using Power BI's Excel integration
- Create pivot tables from the data model
- Use Excel's financial functions for additional analysis

### Teams Integration
- Embed dashboards in Microsoft Teams channels
- Set up alerts for significant portfolio changes
- Share insights through Teams chat

## 📚 Best Practices

1. **Performance Optimization**
   - Use DirectQuery for real-time data when possible
   - Implement row-level security for multi-user scenarios
   - Optimize DAX calculations for better performance

2. **User Experience**
   - Provide clear navigation between dashboard pages
   - Include tooltips explaining complex metrics
   - Ensure consistent filtering across all visuals

3. **Data Governance**
   - Document all custom measures and calculations
   - Implement version control for dashboard changes
   - Regular testing of data accuracy and completeness

## 🆘 Troubleshooting

### Common Issues

**SQLite Connection Problems**
- Verify ODBC driver installation
- Check file path in datasource_config.pq
- Ensure database file permissions

**Data Not Refreshing**
- Confirm Python script has updated the database
- Check Power BI cache settings
- Verify table relationships are intact

**Performance Issues**
- Review query folding in Power Query
- Optimize DAX measures
- Consider data model simplification

## 📞 Support

For technical support with Power BI integration:
1. Check the main project README for general setup issues
2. Review Power BI documentation for platform-specific questions
3. Verify database schema matches expected structure

---

**🎯 Professional Portfolio Analytics at Your Fingertips**

Transform your portfolio data into actionable insights with these Power BI templates designed specifically for the Financial Portfolio Tracker system.