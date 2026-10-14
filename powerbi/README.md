# Power BI report

`PortfolioTracker.pbip` is a Power BI project: the semantic model is stored as
TMDL and the report as PBIR JSON, so both diff cleanly in git instead of
living inside a binary .pbix.

```text
PortfolioTracker.pbip                 open this in Power BI Desktop
PortfolioTracker.SemanticModel/
  definition/tables/*.tmdl            tables, columns, DAX measures, Power Query source
  definition/relationships.tmdl
  definition/expressions.tmdl         ExportFolder parameter + shared CSV loader
PortfolioTracker.Report/
  definition/pages/*/                 one folder per page, one per visual
  StaticResources/RegisteredResources/PortfolioTracker.json   theme
```

## Opening it

1. `python -m tracker refresh` so `exports/powerbi/*.csv` exist.
2. Open `PortfolioTracker.pbip` in Power BI Desktop.
3. If the repo isn't at the path baked into the `ExportFolder` parameter:
   Transform data → Edit parameters → point it at your `exports\powerbi` folder.
4. Refresh.

After that, each Power BI refresh picks up whatever the last Python refresh
wrote. With the scheduled task from `scripts/schedule_refresh.ps1` running,
that's at most 15 minutes behind the market.

The data comes in as CSV rather than straight from SQLite because Power BI
Desktop has no native SQLite connector, and the ODBC route needs a third-party
driver on every machine that opens the report.

## Model

| Table | Grain | Source |
| --- | --- | --- |
| dim_portfolio | portfolio | `portfolio` |
| dim_security | ticker | `security` |
| dim_date | calendar day | built in Power Query from the performance history |
| fact_position | portfolio × ticker | `v_position_live` (closed positions kept, `is_open = 0`) |
| fact_watchlist | ticker | `v_watchlist`, the whole 235-name universe |
| fact_perf_daily | portfolio × trading day | `perf_daily` (TWR index, drawdown, SPY index) |
| fact_trade | trade | `trade` |
| risk_summary | portfolio | `risk_summary` |
| refresh_info | single row | when quotes were last pulled |

All relationships are single-direction, dimension to fact. Measures live on
the fact table they summarise, grouped into display folders (Holdings,
Performance, Market, Formatting).

A few measures worth knowing about:

- **Period Return / SPY Period Return** divide the TWR index at the end of the
  selected window by the index at the start, so a deposit in the middle of the
  window doesn't inflate the return. Blank unless exactly one portfolio is
  selected, since chaining two portfolios' indexes together means nothing.
- **Cumulative Return** rebases to 0% at the start of the date slicer, and
  returns blank on non-trading days so the line doesn't drop to -100% on weekends.
- **Drawdown From Peak** measures from the running peak inside the window, not
  since inception. `risk_summary` has the since-inception number.
- **Position Weight** uses `ALLSELECTED(dim_security)`, so it's the share of
  whatever is on screen: of the portfolio in the holdings table, of a sector
  once a sector is clicked.
- **Move Color / P&L Color** return hex codes, used as field-value conditional
  formatting on the treemap and the tables.

## Pages

- **Overview** - one portfolio at a time: market value, day and unrealized
  P&L, period return against SPY, cumulative return and drawdown lines, sector
  allocation.
- **Holdings** - every open position with shares, average cost, last price,
  weight, unrealized % and day P&L, coloured by sign; weight by sector.
- **Market monitor** - all 235 names: advancers/decliners, median move, how
  many are near their 52-week high, live-quote coverage, a treemap sized by
  30-day traded value and coloured by today's move, and a sortable movers table.
- **Risk** - since-inception return, volatility, Sharpe, max drawdown, beta and
  top-5 concentration per portfolio, with return and drawdown lines and sector
  weights side by side.

Screenshots are in [`../docs/screenshots`](../docs/screenshots).
