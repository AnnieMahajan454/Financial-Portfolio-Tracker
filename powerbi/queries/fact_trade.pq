fnLoadExport("fact_trade", {
    {"trade_id", Int64.Type}, {"portfolio_id", Int64.Type}, {"ticker", type text},
    {"trade_date", type date}, {"side", type text}, {"qty", type number},
    {"price", Currency.Type}, {"fees", Currency.Type}, {"gross_amount", Currency.Type}
})
