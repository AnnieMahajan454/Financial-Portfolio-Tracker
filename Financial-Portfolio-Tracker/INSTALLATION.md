# 🛠️ Installation Guide

## Quick Demo Setup

### Prerequisites
- Python 3.8+
- pip (Python package installer)

### Required Python Packages
```bash
pip install pandas yfinance sqlite3
```

### Run Demo
```bash
python python/demo_database_setup.py
```

## Full Setup Options

### Option 1: SQLite (Recommended for Demo)
- No additional setup required
- Database file created automatically
- Perfect for testing and small projects

### Option 2: PostgreSQL (Production)
- Install PostgreSQL server
- Run SQL scripts from `sql/` folder
- Update connection strings in Python scripts

## Power BI Integration
1. Install Power BI Desktop
2. Import CSV files from `data/` folder
3. Follow Power BI configuration guide in `powerbi/` folder