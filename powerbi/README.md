# Power BI report

The report reads the CSVs that `python -m tracker refresh` writes to
`exports/powerbi/`. I went with CSV instead of connecting straight to SQLite
because Power BI Desktop has no native SQLite connector, and the ODBC route
means installing a third-party driver on every machine that opens the file.

## Wiring it up

1. Run `python -m tracker refresh` once so the CSVs exist.
2. Power BI Desktop → Transform data → New source → Blank query, once per file
   in `queries/`. Paste the file contents into the Advanced Editor and name the
   query after the file (`ExportFolder`, `fnLoadExport`, `fact_position`, ...).
   Set `ExportFolder` to your own `exports\powerbi` path.
3. Close & Apply, then in Model view add the relationships listed at the top of
   `measures.dax`. Before loading, turn off "Autodetect new relationships"
   (Options → Current file → Data load). It matches on the `portfolio` and `name`
   text columns and links the wrong tables.
4. Create the `dim_date` table and the measures from `measures.dax`. Mark
   `dim_date` as the date table.

After that, each refresh in Power BI picks up whatever the last Python refresh
wrote. With the scheduled task from `scripts/schedule_refresh.ps1` running,
that's at most 15 minutes behind the market.

### Optional: direct SQLite over ODBC

If you'd rather skip the CSV step, install the
[SQLite ODBC driver](http://www.ch-werner.de/sqliteodbc/) and use
Get data → ODBC with
`Driver={SQLite3 ODBC Driver};Database=C:\path\to\portfolio.db`. The views
(`v_position_live`, `v_watchlist`, `perf_daily`, ...) have the same columns
as the CSVs, so the measures work unchanged. The database runs in WAL mode, so
Power BI can read it while a refresh is writing.

## Pages

**Overview.** Portfolio slicer and date range across the top. Cards: Market
Value, Day P&L / Day %, Unrealized P&L, Period Return vs SPY Period Return.
Line chart of Cumulative Return and SPY Cumulative Return by `dim_date[Date]`,
with Drawdown as an area chart underneath on the same axis. The `Prices As Of`
measure goes in a small text card in the corner so a stale report is obvious.

**Holdings.** Table by ticker: name, sector, qty, avg cost, price, Market Value,
Weight, Unrealized %, Day P&L. Conditional formatting on Unrealized % and Day
P&L (diverging, centred on zero). Donut of Weight by `dim_security[sector]`.
Cards for Names Held and Top 5 Weight. The Weight measure uses ALLSELECTED, so
it reads as share of the filtered book when a sector is clicked.

**Market monitor.** The full universe of 235 names, held or not. Treemap
grouped by sector, sized by `avg_volume_30d`, coloured by `day_change_pct`.
Cards: Advancers, Decliners, Median Move, Within 2% of 52w High, Live Quote
Coverage. Table of the day's top and bottom 10 movers (TopN visual filter on
`day_change_pct`). An `is_held` slicer narrows it to the names we own.

**Risk.** One row per portfolio from `risk_summary` (total return, annualized
volatility, Sharpe, max drawdown, beta, top-5 concentration), plus a bar chart
of sector Weight per portfolio for comparing concentration across books.

## Colours

Gains `#1A7F37`, losses `#C62828`, neutral and benchmark lines `#6E7781`. The
portfolio line uses `#0B5CAD`. Same colours on every page, so a red number
always means the same thing.
