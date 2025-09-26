"""
Power BI Exporter for Portfolio Tracker

Handles data export to Power BI compatible formats and provides
utilities for creating automated reporting workflows.
"""

import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from .database import DatabaseManager
from .portfolio import PortfolioManager
from .risk_analyzer import RiskAnalyzer


class PowerBIExporter:
    """Exports portfolio data for Power BI consumption."""
    
    def __init__(self, db_manager: DatabaseManager, 
                 portfolio_manager: PortfolioManager,
                 risk_analyzer: RiskAnalyzer,
                 export_path: str = None):
        """Initialize the Power BI exporter.
        
        Args:
            db_manager: Database manager instance
            portfolio_manager: Portfolio manager instance
            risk_analyzer: Risk analyzer instance
            export_path: Base path for data exports
        """
        self.db = db_manager
        self.portfolio_manager = portfolio_manager
        self.risk_analyzer = risk_analyzer
        self.export_path = export_path or 'data/powerbi'
        self.logger = logging.getLogger(__name__)
        
        # Ensure export directory exists
        os.makedirs(self.export_path, exist_ok=True)
    
    def export_portfolio_summary(self, portfolio_ids: List[int] = None) -> str:
        """Export portfolio summary data to CSV.
        
        Args:
            portfolio_ids: List of portfolio IDs to export (None for all)
            
        Returns:
            Path to exported file
        """
        # Get all portfolios if none specified
        if portfolio_ids is None:
            query = "SELECT portfolio_id FROM portfolios WHERE is_active = TRUE"
            result = self.db.execute_query(query)
            portfolio_ids = [row['portfolio_id'] for row in result]
        
        summary_data = []
        
        for portfolio_id in portfolio_ids:
            try:
                summary = self.db.get_portfolio_summary(portfolio_id)
                if summary:
                    performance = self.portfolio_manager.get_portfolio_performance(portfolio_id)
                    
                    combined_data = {
                        'portfolio_id': portfolio_id,
                        'portfolio_name': summary.get('portfolio_name', ''),
                        'user_id': summary.get('user_id', ''),
                        'total_holdings': summary.get('total_holdings', 0),
                        'total_market_value': summary.get('total_market_value', 0),
                        'total_unrealized_pnl': summary.get('total_unrealized_pnl', 0),
                        'base_currency': summary.get('base_currency', 'USD'),
                        'last_updated': summary.get('updated_at', ''),
                        'volatility': performance.get('volatility', 0),
                        'sharpe_ratio': performance.get('sharpe_ratio', 0),
                        'total_return_pct': performance.get('total_return_pct', 0),
                        'export_date': datetime.now().isoformat()
                    }
                    summary_data.append(combined_data)
                    
            except Exception as e:
                self.logger.error(f"Error exporting portfolio {portfolio_id}: {e}")
        
        # Convert to DataFrame and export
        df = pd.DataFrame(summary_data)
        filename = f"portfolio_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(self.export_path, filename)
        
        df.to_csv(filepath, index=False)
        self.logger.info(f"Exported portfolio summary to {filepath}")
        
        return filepath
    
    def export_holdings_detail(self, portfolio_ids: List[int] = None) -> str:
        """Export detailed holdings data to CSV.
        
        Args:
            portfolio_ids: List of portfolio IDs to export
            
        Returns:
            Path to exported file
        """
        if portfolio_ids is None:
            query = "SELECT portfolio_id FROM portfolios WHERE is_active = TRUE"
            result = self.db.execute_query(query)
            portfolio_ids = [row['portfolio_id'] for row in result]
        
        all_holdings = []
        
        for portfolio_id in portfolio_ids:
            try:
                holdings = self.db.get_portfolio_holdings(portfolio_id)
                if not holdings.empty:
                    holdings['export_date'] = datetime.now().isoformat()
                    all_holdings.append(holdings)
                    
            except Exception as e:
                self.logger.error(f"Error exporting holdings for portfolio {portfolio_id}: {e}")
        
        if all_holdings:
            combined_df = pd.concat(all_holdings, ignore_index=True)
            filename = f"holdings_detail_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(self.export_path, filename)
            
            combined_df.to_csv(filepath, index=False)
            self.logger.info(f"Exported holdings detail to {filepath}")
            
            return filepath
        
        return None
    
    def export_risk_metrics(self, portfolio_ids: List[int] = None, 
                          days_back: int = 90) -> str:
        """Export risk metrics data to CSV.
        
        Args:
            portfolio_ids: List of portfolio IDs to export
            days_back: Number of days of historical risk data
            
        Returns:
            Path to exported file
        """
        if portfolio_ids is None:
            query = "SELECT portfolio_id FROM portfolios WHERE is_active = TRUE"
            result = self.db.execute_query(query)
            portfolio_ids = [row['portfolio_id'] for row in result]
        
        all_risk_data = []
        
        for portfolio_id in portfolio_ids:
            try:
                # Get current risk metrics
                current_metrics = self.risk_analyzer.calculate_portfolio_risk_metrics(portfolio_id)
                
                if 'error' not in current_metrics:
                    # Flatten the metrics structure for Power BI
                    flattened_metrics = self._flatten_risk_metrics(current_metrics)
                    all_risk_data.extend(flattened_metrics)
                
                # Get historical trends
                historical_data = self.risk_analyzer.get_risk_trend_analysis(
                    portfolio_id, days_back
                )
                
                if not historical_data.empty:
                    historical_data['portfolio_id'] = portfolio_id
                    all_risk_data.extend(historical_data.to_dict('records'))
                    
            except Exception as e:
                self.logger.error(f"Error exporting risk metrics for portfolio {portfolio_id}: {e}")
        
        if all_risk_data:
            df = pd.DataFrame(all_risk_data)
            filename = f"risk_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(self.export_path, filename)
            
            df.to_csv(filepath, index=False)
            self.logger.info(f"Exported risk metrics to {filepath}")
            
            return filepath
        
        return None
    
    def _flatten_risk_metrics(self, metrics: Dict) -> List[Dict]:
        """Flatten nested risk metrics dictionary for Power BI."""
        flattened = []
        portfolio_id = metrics.get('portfolio_id', 0)
        calculation_date = metrics.get('calculation_date', datetime.now().isoformat())
        
        # Basic metrics
        if 'basic_metrics' in metrics:
            for metric_name, value in metrics['basic_metrics'].items():
                flattened.append({
                    'portfolio_id': portfolio_id,
                    'metric_date': calculation_date,
                    'metric_type': metric_name,
                    'value': value,
                    'confidence_level': None,
                    'category': 'basic'
                })
        
        # VaR metrics
        if 'var_metrics' in metrics:
            for metric_name, value in metrics['var_metrics'].items():
                confidence_level = int(metric_name.split('_')[1]) / 100
                flattened.append({
                    'portfolio_id': portfolio_id,
                    'metric_date': calculation_date,
                    'metric_type': 'var',
                    'value': value,
                    'confidence_level': confidence_level,
                    'category': 'risk'
                })
        
        # CVaR metrics
        if 'cvar_metrics' in metrics:
            for metric_name, value in metrics['cvar_metrics'].items():
                confidence_level = int(metric_name.split('_')[1]) / 100
                flattened.append({
                    'portfolio_id': portfolio_id,
                    'metric_date': calculation_date,
                    'metric_type': 'cvar',
                    'value': value,
                    'confidence_level': confidence_level,
                    'category': 'risk'
                })
        
        # Concentration metrics
        if 'concentration_metrics' in metrics:
            for metric_name, value in metrics['concentration_metrics'].items():
                flattened.append({
                    'portfolio_id': portfolio_id,
                    'metric_date': calculation_date,
                    'metric_type': f'concentration_{metric_name}',
                    'value': value,
                    'confidence_level': None,
                    'category': 'concentration'
                })
        
        return flattened
    
    def export_sector_allocation(self, portfolio_ids: List[int] = None) -> str:
        """Export sector allocation data to CSV.
        
        Args:
            portfolio_ids: List of portfolio IDs to export
            
        Returns:
            Path to exported file
        """
        if portfolio_ids is None:
            query = "SELECT portfolio_id FROM portfolios WHERE is_active = TRUE"
            result = self.db.execute_query(query)
            portfolio_ids = [row['portfolio_id'] for row in result]
        
        all_sector_data = []
        
        for portfolio_id in portfolio_ids:
            try:
                sector_data = self.portfolio_manager.get_sector_allocation(portfolio_id)
                if not sector_data.empty:
                    sector_data['portfolio_id'] = portfolio_id
                    sector_data['export_date'] = datetime.now().isoformat()
                    all_sector_data.append(sector_data)
                    
            except Exception as e:
                self.logger.error(f"Error exporting sector allocation for portfolio {portfolio_id}: {e}")
        
        if all_sector_data:
            combined_df = pd.concat(all_sector_data, ignore_index=True)
            filename = f"sector_allocation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(self.export_path, filename)
            
            combined_df.to_csv(filepath, index=False)
            self.logger.info(f"Exported sector allocation to {filepath}")
            
            return filepath
        
        return None
    
    def export_performance_attribution(self, portfolio_ids: List[int] = None) -> str:
        """Export performance attribution data to CSV.
        
        Args:
            portfolio_ids: List of portfolio IDs to export
            
        Returns:
            Path to exported file
        """
        if portfolio_ids is None:
            query = "SELECT portfolio_id FROM portfolios WHERE is_active = TRUE"
            result = self.db.execute_query(query)
            portfolio_ids = [row['portfolio_id'] for row in result]
        
        all_attribution_data = []
        
        for portfolio_id in portfolio_ids:
            try:
                attribution = self.portfolio_manager.get_performance_attribution(portfolio_id)
                if not attribution.empty:
                    attribution['portfolio_id'] = portfolio_id
                    attribution['export_date'] = datetime.now().isoformat()
                    all_attribution_data.append(attribution)
                    
            except Exception as e:
                self.logger.error(f"Error exporting performance attribution for portfolio {portfolio_id}: {e}")
        
        if all_attribution_data:
            combined_df = pd.concat(all_attribution_data, ignore_index=True)
            filename = f"performance_attribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(self.export_path, filename)
            
            combined_df.to_csv(filepath, index=False)
            self.logger.info(f"Exported performance attribution to {filepath}")
            
            return filepath
        
        return None
    
    def create_full_export_package(self, portfolio_ids: List[int] = None) -> Dict[str, str]:
        """Create a complete export package for Power BI.
        
        Args:
            portfolio_ids: List of portfolio IDs to export
            
        Returns:
            Dictionary with file paths for all exported data
        """
        export_files = {}
        
        # Export all data types
        try:
            export_files['portfolio_summary'] = self.export_portfolio_summary(portfolio_ids)
        except Exception as e:
            self.logger.error(f"Error exporting portfolio summary: {e}")
        
        try:
            export_files['holdings_detail'] = self.export_holdings_detail(portfolio_ids)
        except Exception as e:
            self.logger.error(f"Error exporting holdings detail: {e}")
        
        try:
            export_files['risk_metrics'] = self.export_risk_metrics(portfolio_ids)
        except Exception as e:
            self.logger.error(f"Error exporting risk metrics: {e}")
        
        try:
            export_files['sector_allocation'] = self.export_sector_allocation(portfolio_ids)
        except Exception as e:
            self.logger.error(f"Error exporting sector allocation: {e}")
        
        try:
            export_files['performance_attribution'] = self.export_performance_attribution(portfolio_ids)
        except Exception as e:
            self.logger.error(f"Error exporting performance attribution: {e}")
        
        # Create manifest file
        manifest = {
            'export_timestamp': datetime.now().isoformat(),
            'portfolio_ids': portfolio_ids,
            'files': {k: v for k, v in export_files.items() if v is not None}
        }
        
        manifest_file = os.path.join(self.export_path, f"export_manifest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        export_files['manifest'] = manifest_file
        
        self.logger.info(f"Created full export package with {len(export_files)} files")
        
        return export_files
    
    def create_powerbi_template_config(self) -> str:
        """Create a Power BI template configuration file.
        
        Returns:
            Path to configuration file
        """
        config = {
            "version": "1.0",
            "data_sources": {
                "portfolio_summary": {
                    "file_pattern": "portfolio_summary_*.csv",
                    "key_columns": ["portfolio_id"],
                    "refresh_frequency": "daily"
                },
                "holdings_detail": {
                    "file_pattern": "holdings_detail_*.csv",
                    "key_columns": ["portfolio_id", "symbol"],
                    "refresh_frequency": "daily"
                },
                "risk_metrics": {
                    "file_pattern": "risk_metrics_*.csv",
                    "key_columns": ["portfolio_id", "metric_date", "metric_type"],
                    "refresh_frequency": "daily"
                },
                "sector_allocation": {
                    "file_pattern": "sector_allocation_*.csv",
                    "key_columns": ["portfolio_id", "sector"],
                    "refresh_frequency": "daily"
                },
                "performance_attribution": {
                    "file_pattern": "performance_attribution_*.csv",
                    "key_columns": ["portfolio_id", "symbol"],
                    "refresh_frequency": "daily"
                }
            },
            "measures": {
                "total_portfolio_value": "SUM(portfolio_summary[total_market_value])",
                "total_unrealized_pnl": "SUM(portfolio_summary[total_unrealized_pnl])",
                "avg_sharpe_ratio": "AVERAGE(portfolio_summary[sharpe_ratio])",
                "portfolio_count": "DISTINCTCOUNT(portfolio_summary[portfolio_id])",
                "top_performing_sector": "TOPN(1, sector_allocation, [sector_value])"
            },
            "dashboard_layout": {
                "overview": {
                    "widgets": [
                        {"type": "card", "measure": "total_portfolio_value"},
                        {"type": "card", "measure": "total_unrealized_pnl"},
                        {"type": "card", "measure": "portfolio_count"},
                        {"type": "chart", "chart_type": "pie", "data": "sector_allocation"}
                    ]
                },
                "risk_analysis": {
                    "widgets": [
                        {"type": "chart", "chart_type": "line", "data": "risk_metrics"},
                        {"type": "table", "data": "risk_metrics"},
                        {"type": "chart", "chart_type": "bar", "data": "sector_allocation"}
                    ]
                },
                "performance": {
                    "widgets": [
                        {"type": "chart", "chart_type": "waterfall", "data": "performance_attribution"},
                        {"type": "table", "data": "holdings_detail"},
                        {"type": "chart", "chart_type": "scatter", "data": "portfolio_summary"}
                    ]
                }
            }
        }
        
        config_file = os.path.join(self.export_path, "powerbi_template_config.json")
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.logger.info(f"Created Power BI template configuration: {config_file}")
        
        return config_file
    
    def schedule_automated_export(self, portfolio_ids: List[int] = None,
                                frequency: str = 'daily',
                                time_of_day: str = '06:00') -> str:
        """Create configuration for automated exports.
        
        Args:
            portfolio_ids: List of portfolio IDs to export
            frequency: Export frequency ('daily', 'weekly', 'monthly')
            time_of_day: Time to run export (HH:MM format)
            
        Returns:
            Path to scheduling configuration file
        """
        schedule_config = {
            "export_job": {
                "name": "portfolio_data_export",
                "description": "Automated export of portfolio data for Power BI",
                "frequency": frequency,
                "time": time_of_day,
                "portfolio_ids": portfolio_ids,
                "export_path": self.export_path,
                "retention_days": 30,  # Keep exports for 30 days
                "notification_email": None,  # Configure as needed
                "enabled": True
            },
            "export_types": [
                "portfolio_summary",
                "holdings_detail", 
                "risk_metrics",
                "sector_allocation",
                "performance_attribution"
            ],
            "created_at": datetime.now().isoformat()
        }
        
        schedule_file = os.path.join(self.export_path, "automated_export_schedule.json")
        
        with open(schedule_file, 'w') as f:
            json.dump(schedule_config, f, indent=2)
        
        self.logger.info(f"Created automated export schedule: {schedule_file}")
        
        return schedule_file
