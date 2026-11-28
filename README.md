# DearCyFi_Demo

## Chart Snapshot Walkthrough

1. On the DearCyFi tab, load candles and bars, add two SMAs and a box, then
   collapse time and zoom. Hide one series by clicking its legend entry.
2. Start the synthetic stream. Right-click the plot, choose **Save Chart...**,
   enter a local path, and save. Saving does not stop the stream. Repeat with
   the same path and cancel at the overwrite prompt to keep the first file.
3. Right-click and choose **Open Chart...**. Try a missing file and verify the
   error allows a retry and the stream continues. Choose the saved file and
   cancel at the replacement prompt; the chart and stream should be unchanged.
4. Open the saved file and confirm replacement. The stream stops, the saved
   view returns, and the restored boxes and SMA controls are usable. The series
   hidden in step 1 is visible again and can still be toggled from the legend.
   Check the original-time tab: Open did not replace that plot.
5. Toggle collapse off, try the remaining right-click controls, and reload
   candles or econometric data explicitly to resume normal provider workflows.

The JSON contains the saved observations. Use synthetic data for files you
intend to share, or verify your data-sharing rights first.
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
the weekly series with a chosen observation count and seed. Collapse and gap
controls are owned by the chart's native plot context menu.

Right-click a candle or liquidity legend entry to see that series' label and
unique item ID immediately. Select **Identify this series** to show the
originating plot, label, and ID in that menu and the Status Text panel. The
original-time candle legend has the same probe.

Candles use the price scale on `Y1`. The weekly line and its markers use the
enabled, independently fitted `Y3` scale labeled "Econometric Value". Optional
date-label diagnostics retain their existing `Y2` reservation.

Right-click the chart and use **Collapse Time** to project both series through
the candle-derived map. **Vectorized Collapse** is selected by default; clearing
it makes the next collapse use the scalar method. Hover a weekly marker to inspect
its original source date and value. Uncheck **Collapse Time** to restore real
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

## Candle Indicator Walkthrough

1. Open **Candle Indicators** in the left panel. SMA is selected by default;
   choose a period and `Open`, `High`, `Low`, or `Close`, then select **Add**.
   Choose a line color with the color editor; each added indicator keeps its
   own color.
   Repeat to add another independent instance, including matching parameters.
   The legend entry appears immediately, but the SMA has no values until it
   has a full period of candle observations.
2. Right-click an indicator legend entry. Use **Edit indicator** to open a
   prefilled popup, change the period, OHLC field, or line color, and select
   **Apply**.
   Invalid Apply values remain in the popup and report an error. **Cancel**
   leaves the instance unchanged.
3. Start synthetic streaming, or toggle **Gap next appended candle**, while
   indicator popups and legend menus are open. Revisions and appends keep the
   indicator values synchronized; gap timestamps do not create extra SMA
   observations.
4. Collapse time and restore time while indicators remain present. An indicator
   follows the active collapse map and tooltip dates remain original candle
   timestamps. Reload candles or change the toy symbol to recalculate indicators
   from replacement data.
5. Select **Remove indicator** from the legend menu to unregister, delete, and
   clean up only that instance. The original-time comparison plot never gains
   indicator items.
