fnLoadExport("fact_perf_daily", {
    {"portfolio_id", Int64.Type}, {"bar_date", type date}, {"market_value", Currency.Type},
    {"net_flow", Currency.Type}, {"daily_return", type number}, {"twr_index", type number},
    {"drawdown", Percentage.Type}, {"bench_index", type number}
})
