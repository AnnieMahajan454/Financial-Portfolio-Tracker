// Power BI Data Source Configuration
// Financial Portfolio Tracker

// PostgreSQL Database Connection
let
    DatabaseServer = "localhost",
    DatabasePort = 5432,
    DatabaseName = "portfolio_tracker",
    Source = PostgreSQL.Database(DatabaseServer, DatabaseName)
in
    Source