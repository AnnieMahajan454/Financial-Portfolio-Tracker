fnLoadExport("fact_position", {
    {"portfolio_id", Int64.Type}, {"portfolio", type text}, {"ticker", type text},
    {"name", type text}, {"sector", type text}, {"qty", type number},
    {"avg_cost", Currency.Type}, {"opened_on", type date}, {"cost_basis", Currency.Type},
    {"price", Currency.Type}, {"prev_close", Currency.Type}, {"market_value", Currency.Type},
    {"unrealized_pnl", Currency.Type}, {"unrealized_pct", Percentage.Type},
    {"day_pnl", Currency.Type}, {"weight", Percentage.Type}, {"realized_pnl", Currency.Type},
    {"is_open", Int64.Type}, {"price_source", type text}, {"price_time", type text}
})
