// Power BI Data Source Configuration for Financial Portfolio Tracker
// This file contains Power Query M code for connecting to the SQLite database

let
    // Database connection parameters
    DatabasePath = "C:\Path\To\Your\portfolio.db",  // Update this path
    
    // Connect to SQLite database
    Source = Sqlite.Database(File.Contents(DatabasePath)),
    
    // Import main tables
    portfolios = Source{[Schema="",Item="portfolios"]}[Data],
    positions = Source{[Schema="",Item="positions"]}[Data],
    securities = Source{[Schema="",Item="securities"]}[Data],
    transactions = Source{[Schema="",Item="transactions"]}[Data],
    market_data = Source{[Schema="",Item="market_data"]}[Data],
    
    // Import analytics views
    portfolio_summary = Source{[Schema="",Item="portfolio_summary"]}[Data],
    top_holdings = Source{[Schema="",Item="top_holdings"]}[Data],
    winners_losers = Source{[Schema="",Item="winners_losers"]}[Data],
    sector_allocation = Source{[Schema="",Item="sector_allocation"]}[Data],
    risk_metrics = Source{[Schema="",Item="risk_metrics"]}[Data],
    
    // Data transformations for better Power BI integration
    
    // Transform portfolios data
    portfolios_transformed = Table.TransformColumns(portfolios,{
        {"created_date", each DateTime.From(_), type datetime},
        {"last_updated", each DateTime.From(_), type datetime}
    }),
    
    // Transform positions with calculated fields
    positions_transformed = 
        let
            addMarketData = Table.NestedJoin(positions, {"symbol"}, market_data, {"symbol"}, "market_data", JoinKind.LeftOuter),
            expandMarketData = Table.ExpandTableColumn(addMarketData, "market_data", {"price"}, {"current_price"}),
            addCalculatedFields = Table.AddColumn(expandMarketData, "market_value", each [quantity] * List.First({[current_price], [avg_cost]})),
            addUnrealizedPL = Table.AddColumn(addCalculatedFields, "unrealized_pl", each [market_value] - ([quantity] * [avg_cost])),
            addReturnPercent = Table.AddColumn(addUnrealizedPL, "return_percent", each if [avg_cost] <> 0 then (([current_price] / [avg_cost]) - 1) * 100 else 0)
        in
            addReturnPercent,
    
    // Transform transactions data
    transactions_transformed = Table.TransformColumns(transactions,{
        {"transaction_date", each DateTime.From(_), type datetime},
        {"price", Currency.From, Currency.Type},
        {"quantity", Number.From, type number}
    }),
    
    // Add total value calculation
    transactions_with_total = Table.AddColumn(transactions_transformed, "total_value", each [quantity] * [price]),
    
    // Transform market data with proper data types
    market_data_transformed = Table.TransformColumns(market_data,{
        {"price", Currency.From, Currency.Type},
        {"timestamp", each DateTime.From(_), type datetime},
        {"volume", Int64.From, Int64.Type}
    }),
    
    // Create comprehensive dataset for dashboard
    comprehensive_data = 
        let
            joinPositionsPortfolios = Table.NestedJoin(positions_transformed, {"portfolio_id"}, portfolios_transformed, {"portfolio_id"}, "portfolio", JoinKind.LeftOuter),
            expandPortfolios = Table.ExpandTableColumn(joinPositionsPortfolios, "portfolio", {"name", "investment_style", "risk_tolerance"}, {"portfolio_name", "investment_style", "risk_tolerance"}),
            joinSecurities = Table.NestedJoin(expandPortfolios, {"symbol"}, securities, {"symbol"}, "security", JoinKind.LeftOuter),
            expandSecurities = Table.ExpandTableColumn(joinSecurities, "security", {"company_name", "sector", "industry"}, {"company_name", "sector", "industry"})
        in
            expandSecurities

in
    // Return the comprehensive dataset as the main table
    comprehensive_data

// Additional helper queries for specific dashboards:

// Query for Portfolio Performance Dashboard
PortfolioPerformance = 
    let
        Source = portfolio_summary,
        AddKPIs = Table.AddColumn(Source, "performance_status", 
            each if [total_return_percent] > 10 then "Excellent"
                 else if [total_return_percent] > 5 then "Good" 
                 else if [total_return_percent] > 0 then "Positive"
                 else if [total_return_percent] > -10 then "Poor"
                 else "Very Poor")
    in
        AddKPIs,

// Query for Sector Analysis
SectorAnalysis = 
    let
        Source = sector_allocation,
        AddRanking = Table.AddIndexColumn(Table.Sort(Source, {{"allocation_percent", Order.Descending}}), "sector_rank", 1)
    in
        AddRanking,

// Query for Risk Dashboard
RiskAnalysis = 
    let
        Source = risk_metrics,
        AddRiskLevel = Table.AddColumn(Source, "risk_level",
            each if [avg_beta] > 1.5 then "High Risk"
                 else if [avg_beta] > 1.0 then "Medium Risk"
                 else if [avg_beta] > 0.5 then "Low Risk"
                 else "Very Low Risk")
    in
        AddRiskLevel