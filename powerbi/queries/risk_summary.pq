fnLoadExport("risk_summary", {
    {"portfolio_id", Int64.Type}, {"as_of", type date}, {"days", Int64.Type},
    {"total_return", Percentage.Type}, {"ann_volatility", Percentage.Type},
    {"sharpe", type number}, {"max_drawdown", Percentage.Type}, {"beta", type number},
    {"top5_weight", Percentage.Type}
})
