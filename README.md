# DearCyFi_Demo
A GUI App for testing and showcasing DearCyFi

This demo requires the custom DearCyGui build that provides
`dcg.PlotColorBars`. Candle volume is direction-colored and normalized to a
stable bottom-anchored fraction of plot height. The **Bar Length Mode** control
switches the sample horizontal overlay between data and normalized lengths.
Horizontal sizing is intentionally approximate until volume-weighted price
sampling is implemented.

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
date and value. Use **Restore Time** in Collapsing Controls to restore real
coordinates without reloading or discarding streamed data. The current view is
not automatically fitted, so pan or fit the chart if restored data moves outside
the visible range.

## Synthetic Candle Streaming Walkthrough

1. Load a candle dataset with at least two observations, then note the displayed
   candle interval. The stream uses a seeded, repeatable synthetic generator
   and does not connect to a provider.
2. Set **Synthetic stream update period** to a short delay and start the stream.
   The latest candle is revised several times before a new candle is appended.
   The original-time comparison plot receives the same OHLCV observations.
3. Toggle **Gap next appended candle** before the next append to add a 2.5
   interval gap. Collapse time before or after streaming to inspect the new
   source-map tail and the weekly econometric follower. Also try `previous` /
   `next` follower behavior by changing its registration policy in the demo
   source.
4. Click **Restore Time** and verify that the source timestamps, streamed
   candles, and both plots remain synchronized. Start and stop repeatedly, then
   reload candles or select a different toy symbol while streaming; the producer
   must stop before the replacement data is loaded.

The stream never auto-fits or scrolls either chart. Its status control reports
running, stopped, and mutation-error states. A failed chart update stops the
producer rather than skipping the event.
