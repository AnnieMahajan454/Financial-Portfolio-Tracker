"""
Basic Portfolio Example

This example demonstrates the core functionality of the Financial Portfolio Tracker:
1. Creating a portfolio
2. Adding holdings
3. Updating prices
4. Calculating performance and risk metrics
5. Exporting data for Power BI
"""

import os
import sys
import logging
from datetime import datetime

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from portfolio_tracker import (
    DatabaseManager, 
    PortfolioManager, 
    DataFetcher, 
    RiskAnalyzer, 
    PowerBIExporter
)


def setup_logging():
    """Set up basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/portfolio_example.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def main():
    """Main example function."""
    logger = setup_logging()
    logger.info("Starting Portfolio Tracker Example")
    
    # Database configuration (adjust as needed)
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'portfolio_tracker',
        'user': 'portfolio_user',
        'password': 'your_password'  # Use environment variable in production
    }
    
    try:
        # Initialize components
        logger.info("Initializing components...")
        db_manager = DatabaseManager(db_config)
        data_fetcher = DataFetcher()  # Uses Yahoo Finance by default
        portfolio_manager = PortfolioManager(db_manager, data_fetcher)
        risk_analyzer = RiskAnalyzer(db_manager, data_fetcher)
        powerbi_exporter = PowerBIExporter(db_manager, portfolio_manager, risk_analyzer)
        
        # Step 1: Create a new portfolio
        logger.info("Creating a new portfolio...")
        portfolio_id = portfolio_manager.create_portfolio(
            user_id=1,
            name="Sample Tech Portfolio",
            description="A diversified technology portfolio for demonstration purposes"
        )
        logger.info(f"Created portfolio with ID: {portfolio_id}")
        
        # Step 2: Add sample holdings
        logger.info("Adding holdings to portfolio...")
        holdings_to_add = [
            ("AAPL", 100, 150.00, "2023-01-15"),  # Apple
            ("MSFT", 75, 280.00, "2023-01-20"),   # Microsoft
            ("GOOGL", 30, 2200.00, "2023-02-01"), # Google
            ("AMZN", 40, 3100.00, "2023-02-10"),  # Amazon
            ("TSLA", 50, 800.00, "2023-02-15"),   # Tesla
            ("NVDA", 25, 400.00, "2023-03-01"),   # NVIDIA
            ("META", 60, 220.00, "2023-03-05"),   # Meta
            ("NFLX", 35, 350.00, "2023-03-10"),   # Netflix
        ]
        
        for symbol, quantity, cost, purchase_date in holdings_to_add:
            try:
                holding_id = portfolio_manager.add_holding(
                    portfolio_id, symbol, quantity, cost, purchase_date
                )
                logger.info(f"Added holding: {symbol} - {quantity} shares at ${cost}")
            except Exception as e:
                logger.error(f"Error adding holding {symbol}: {e}")
        
        # Step 3: Update current prices
        logger.info("Updating portfolio prices...")
        update_result = portfolio_manager.update_portfolio_prices(portfolio_id)
        logger.info(f"Price update result: {update_result}")
        
        # Step 4: Get portfolio performance
        logger.info("Calculating portfolio performance...")
        performance = portfolio_manager.get_portfolio_performance(portfolio_id)
        
        if 'error' not in performance:
            print("\n" + "="*50)
            print("PORTFOLIO PERFORMANCE SUMMARY")
            print("="*50)
            print(f"Total Market Value: ${performance['total_market_value']:,.2f}")
            print(f"Total Cost Basis: ${performance['total_cost']:,.2f}")
            print(f"Total P&L: ${performance['total_unrealized_pnl']:,.2f}")
            print(f"Total Return: {performance['total_return_pct']:.2f}%")
            print(f"Volatility: {performance['volatility']:.2f}%")
            print(f"Sharpe Ratio: {performance['sharpe_ratio']:.3f}")
            print(f"Number of Holdings: {performance['num_holdings']}")
            print("="*50)
        else:
            logger.error(f"Error calculating performance: {performance}")
        
        # Step 5: Calculate risk metrics
        logger.info("Calculating risk metrics...")
        risk_metrics = risk_analyzer.calculate_portfolio_risk_metrics(portfolio_id)
        
        if 'error' not in risk_metrics:
            print("\nRISK ANALYSIS")
            print("="*50)
            print(f"Portfolio Beta: {risk_metrics['basic_metrics']['beta']:.3f}")
            print(f"VaR (95%): {risk_metrics['var_metrics']['var_95']:.2f}%")
            print(f"VaR (99%): {risk_metrics['var_metrics']['var_99']:.2f}%")
            print(f"CVaR (95%): {risk_metrics['cvar_metrics']['cvar_95']:.2f}%")
            print(f"Max Drawdown: {risk_metrics['basic_metrics']['max_drawdown']:.2f}%")
            print(f"Sortino Ratio: {risk_metrics['basic_metrics']['sortino_ratio']:.3f}")
            
            # Concentration metrics
            conc_metrics = risk_metrics.get('concentration_metrics', {})
            if conc_metrics:
                print(f"\nCONCENTRATION METRICS")
                print(f"Herfindahl Index: {conc_metrics.get('herfindahl_index', 0):.3f}")
                print(f"Effective Holdings: {conc_metrics.get('effective_holdings', 0):.1f}")
                print(f"Top 5 Concentration: {conc_metrics.get('top_5_concentration', 0):.1f}%")
            
            print("="*50)
        else:
            logger.error(f"Error calculating risk metrics: {risk_metrics}")
        
        # Step 6: Get sector allocation
        logger.info("Analyzing sector allocation...")
        sector_allocation = portfolio_manager.get_sector_allocation(portfolio_id)
        
        if not sector_allocation.empty:
            print("\nSECTOR ALLOCATION")
            print("="*50)
            for _, sector in sector_allocation.iterrows():
                print(f"{sector['sector']:<20}: {sector['sector_weight']:.1f}% (${sector['sector_value']:,.0f})")
            print("="*50)
        
        # Step 7: Get top holdings
        logger.info("Getting top holdings...")
        top_holdings = portfolio_manager.get_top_holdings(portfolio_id, limit=5)
        
        if not top_holdings.empty:
            print("\nTOP 5 HOLDINGS")
            print("="*70)
            print(f"{'Symbol':<8} {'Company':<20} {'Value':<12} {'Weight':<8} {'Return':<8}")
            print("-"*70)
            for _, holding in top_holdings.iterrows():
                return_pct = holding.get('return_pct', 0)
                print(f"{holding['symbol']:<8} {holding['company_name'][:19]:<20} "
                      f"${holding['market_value']:>10,.0f} {holding['weight_percentage']:>6.1f}% "
                      f"{return_pct:>6.1f}%")
            print("="*70)
        
        # Step 8: Stress testing
        logger.info("Running stress tests...")
        stress_results = risk_analyzer.calculate_stress_test_scenarios(portfolio_id)
        
        if 'error' not in stress_results:
            print("\nSTRESS TEST SCENARIOS")
            print("="*60)
            for scenario_name, results in stress_results['stress_scenarios'].items():
                print(f"{scenario_name.replace('_', ' ').title():<25}: "
                      f"{results['portfolio_loss_pct']:>6.1f}% "
                      f"(${results['portfolio_value_loss']:>10,.0f} loss)")
            print("="*60)
        
        # Step 9: Export data for Power BI
        logger.info("Exporting data for Power BI...")
        export_files = powerbi_exporter.create_full_export_package([portfolio_id])
        
        print("\nPOWER BI EXPORT FILES")
        print("="*50)
        for export_type, file_path in export_files.items():
            if file_path:
                print(f"{export_type.replace('_', ' ').title():<25}: {os.path.basename(file_path)}")
        print("="*50)
        
        # Step 10: Save risk metrics to database
        logger.info("Saving risk metrics to database...")
        if 'error' not in risk_metrics:
            records_saved = risk_analyzer.save_risk_metrics(portfolio_id, risk_metrics)
            logger.info(f"Saved {records_saved} risk metric records to database")
        
        logger.info("Portfolio example completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in portfolio example: {e}")
        raise


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Run the example
    main()
