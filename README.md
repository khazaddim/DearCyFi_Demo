# DearCyFi_Demo
A GUI App for testing and showcasing DearCyFi

## Econometric Collapse Scenario

Run `DearCyFi_Demo.py`. The initial chart loads hourly candles as the
`"candles"` collapse source and a deterministic 52-observation weekly liquidity
line as the `"toy-econometric"` follower. The Econometric Data panel can reload
the weekly series with a chosen observation count and seed. The Collapsing
Controls panel displays the active source.

Candles use the price scale on `Y1`. The weekly line and its markers use the
enabled, independently fitted `Y3` scale labeled "Econometric Value". Optional
date-label diagnostics retain their existing `Y2` reservation.

Use **Collapse Time** or **Collapse Time Vec** to project both series through
the candle-derived map. Hover a weekly marker to inspect its original source
date and value. Reloading candle data or calling `restore_time_chart()` restores
real coordinates before another collapse.
