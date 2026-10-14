fnLoadExport("fact_watchlist", {
    {"ticker", type text}, {"name", type text}, {"sector", type text},
    {"price", Currency.Type}, {"prev_close", Currency.Type}, {"day_change", Currency.Type},
    {"day_change_pct", Percentage.Type}, {"day_volume", Int64.Type},
    {"avg_volume_30d", type number}, {"high_52w", Currency.Type}, {"low_52w", Currency.Type},
    {"pct_off_high", Percentage.Type}, {"price_source", type text}, {"price_time", type text},
    {"is_held", Int64.Type}
})
