// Financial Portfolio Tracker - Power BI Data Source Configuration
// ================================================================
// Power Query M language configuration for connecting to CSV data exports

let
    // Define data folder path (adjust as needed)
    DataFolderPath = "data/",
    
    // Portfolio Holdings data
    PortfolioHoldings = Csv.Document(File.Contents(DataFolderPath & "portfolio_holdings.csv"), [Delimiter=",", Columns=null, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    
    // Portfolio Summary data  
    PortfolioSummary = Csv.Document(File.Contents(DataFolderPath & "portfolio_summary.csv"), [Delimiter=",", Columns=null, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    
    // Sector Allocation data
    SectorAllocation = Csv.Document(File.Contents(DataFolderPath & "sector_allocation.csv"), [Delimiter=",", Columns=null, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    
    // Price History data
    PriceHistory = Csv.Document(File.Contents(DataFolderPath & "price_history.csv"), [Delimiter=",", Columns=null, Encoding=65001, QuoteStyle=QuoteStyle.None])

in
    [
        Holdings = PortfolioHoldings,
        Summary = PortfolioSummary, 
        Sectors = SectorAllocation,
        Prices = PriceHistory
    ]