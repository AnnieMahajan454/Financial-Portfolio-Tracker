@echo off
REM Financial Portfolio Tracker - Main Automation Script

echo Starting Portfolio Tracker automation...

cd python
python market_data_fetcher.py
python portfolio_analytics.py

echo Portfolio Tracker execution complete!