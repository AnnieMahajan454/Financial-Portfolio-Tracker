@echo off
REM Database Setup Script for Financial Portfolio Tracker

echo Setting up PostgreSQL database for Portfolio Tracker...

psql -h localhost -p 5432 -U postgres -d postgres -c "CREATE DATABASE portfolio_tracker;"
psql -h localhost -p 5432 -U postgres -d portfolio_tracker -f sql\01_create_database_schema.sql
psql -h localhost -p 5432 -U postgres -d portfolio_tracker -f sql\02_populate_reference_data.sql

echo Database setup complete!