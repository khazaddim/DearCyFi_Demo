"""DearCyFi demo GUI.

Usage notes:
- Host apps feed fresh candle arrays into `DearCyFi` via `set_data(...)`.
- Time-collapse actions are invoked on the plot object (`collapse_time_chart`,
  `collapse_time_chart_vec`) instead of host-managed gap/locator objects.

New shared string stuffs:

# In your overlay window with a semi-transparent theme:
dcg.Text(self.C, shareable_value=self.DCF_plot.debug_text, wrap=400)
"""

import asyncio
import importlib
from datetime import datetime

import dearcygui as dcg
from dearcygui.utils.asyncio_helpers import AsyncPoolExecutor, run_viewport_loop

from demo_widgets import DateTimePicker

from dearcyfi import DearCyFi
from dearcyfi.candle_utils.candle_gen import generate_fake_candlestick_data

from dearcyfi.DCG_Candle_Utils import PlotCandleStick

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


class DearCyFiDemo:
    def __init__(self, white_theme: bool = False):
        self.C = dcg.Context()
        self.C.queue = AsyncPoolExecutor()
        self.C.viewport.wait_for_input = True

        if white_theme:
            self.C.viewport.initialize(height=900, width=1600, theme=self._white_theme())
        else:
            self.C.viewport.initialize(height=900, width=1600)

        with dcg.Window(self.C, label="DearCyFi Demo", primary=True, width="fillx", height="filly") as main_window:
            with dcg.HorizontalLayout(self.C, no_wrap=True):
                with dcg.ChildWindow(self.C, label="Left Side", width=320, resizable_x=True) as self.left_win:
                    self.plot_button = dcg.Button(
                        self.C,
                        label="Reload Candle Data",
                        width="fillx",
                        height='main_window.height/24+10', #32
                        callback=self.plot_candle_data,
                    )
                    # Under the plot candle data button we want to add some controls that will allow us to:
                    # 1. remove or not remove weekends from the time series
                    # 2. remove or not remove overnight gaps from the time series (from 4pm to 9:30am the next day)
                    # 3. change between weekly, daily, hourly, 15 minutes, and 5 minute data intervals
                    # This will be accomplished with a combination of checkboxes and radiobuttons
                    # We will want to have some kind of layout for these controls that makes them look nice and organized under the plot candle data button
                    with dcg.ChildWindow(self.C, label="Instructions", width="fillx", height=400) as inst:
                        with dcg.HorizontalLayout(self.C, no_wrap=True):
                            with dcg.ChildWindow(self.C, label="Gaps Controls", width='inst.width/2', height='filly'):
                                self.gaps_label = dcg.Text(self.C, value="Time Gap Removal:")
                                self.remove_weekends_checkbox = dcg.Checkbox(
                                    self.C,
                                    label="No Weekends",
                                    value=True
                                )
                                self.remove_overnight_gaps_checkbox = dcg.Checkbox(
                                    self.C,
                                    label="No Overnight"
                                )
                            with dcg.ChildWindow(self.C, label="Interval Controls",width="fillx", height='filly'):
                                dcg.Text(self.C, value="Data Interval:")
                                self.interval_radio = dcg.RadioButton(
                                    self.C,
                                    items=["Weekly", "Daily", "Hourly", "15 Min", "5 Min", "Minute"],
                                    value="Hourly",
                                )
                                dcg.Text(self.C, value="Start Date:")
                                self.start_date_button = dcg.Button(
                                    self.C,
                                    label="Default (2024-08-05)",
                                    width="fillx",
                                    callback=self._open_start_date_popup,
                                )
                                
                    self.gaps_button = dcg.Button(
                        self.C,
                        label="Gaps n' Chunks",
                        width="fillx",
                        height='main_window.height/24+10', #32
                        callback=lambda s, a, u: self.DCF_plot.add_gaps_chunks_GUI(s, a, u),
                    )
                    self.collapse_button = dcg.Button(
                        self.C,
                        label="Collapse Time",
                        width="fillx",
                        height='main_window.height/24+10', #32
                        callback=lambda s, a, u: self.DCF_plot.collapse_time_chart(s, a, u),
                    )
                    self.collapse_vec_button = dcg.Button(
                        self.C,
                        label="Collapse Time Vec",
                        width="fillx",
                        height='main_window.height/24+10', #32
                        callback=lambda s, a, u: self.DCF_plot.collapse_time_chart_vec(s, a, u),
                    )
                    # Make a checkbox to toggle the injection of extra labels
                    self.extra_labels_checkbox = dcg.Checkbox(
                        self.C,
                        label="Extra Labels at Segment Starts",
                        value=False,
                        callback=lambda s, a, u: setattr(self.DCF_plot, 'inject_boundary_ticks', s.value)
                    )

                    self.overlap_debug_checkbox = dcg.Checkbox(
                        self.C,
                        label="Label Overlap Diagnostic",
                        value=False,
                        callback=lambda s, a, u: setattr(self.DCF_plot, 'label_overlap_debug', s.value)
                    )

                    self.load_bars_button = dcg.Button(
                        self.C,
                        label="Load Bar Data",
                        width="fillx",
                        height='main_window.height/24+10', #32
                        callback=lambda s, a, u: self.DCF_plot.load_horizontal_bars(s, a, u),
                    )

                    self.status_text = dcg.SharedStr(
                        self.C,
                        value=(
                            "DearCyFi demo loaded.\n"
                            "Click 'Plot Candle Data' to load synthetic candles."
                        ),
                    )
                    self.status_label = dcg.Text(
                        self.C,
                        shareable_value=self.status_text,
                        wrap=300,
                        height="filly",
                    )

                with dcg.ChildWindow(self.C, label="Right Side"):
                    with dcg.TabBar(self.C):
                        # The DearCyFi plot is the main attraction of this demo
                        # The demo shows how it can remove arbitrary time gaps from a candlestick chart
                        # and maintain proper time labels.  Great for equity charts with large time gaps on non-trading days.
                        with dcg.Tab(self.C, label="Collapsed Time Chart"):
                            self.DCF_plot = DearCyFi(
                                self.C,
                                label="DearCyFi Plot",
                                width="fillx",
                                height="filly",
                                has_box_select=True,
                                on_status=self.set_status,
                            )

                        # Original time chart is a normal ImPlot based candle plot in dearcygui
                        # to demonstrate the difference in how the DearCyFi plot and a normal time chart handle large candle datasets and time collapse actions.
                        with dcg.Tab(self.C, label="Original Time Chart"):
                            with dcg.Plot(self.C, label="Original Time Plot", width="fillx", height="filly", has_box_select=True) as self.orig_plot:
                                self.orig_plot.X1.label = "Date"
                                self.orig_plot.X1.scale = dcg.AxisScale.TIME
                                self.orig_plot.Y1.label = "Price ($)"

        # Create floating debug window at top level (not inside primary window)
        with dcg.Window(self.C, label="floating debug window", width="viewport.width/5", height="viewport.height/3", x="viewport.width-(viewport.width / 4)", y="100", no_title_bar=True, no_resize=True, no_move=True, no_scrollbar=True, no_collapse=True) as debug_window:
            debug_window.theme = dcg.ThemeColorImGui(
                self.C,
                border_shadow=(0.1, 0.1, 0.1, 0.0),
                window_bg=(0.1, 0.1, 0.12, 0.7),  # Dark gray, 70% opacity
                title_bg=(0.15, 0.15, 0.15, 0.8),
                text=(0.3, 0.9, 0.4, 1.0),  # Bright green text
            )
            # Wire into DearCyFi's shared debug string
            dcg.Text(self.C, shareable_value=self.DCF_plot.debug_text, wrap=300)

        self.left_win.handlers += [
            dcg.ResizeHandler(self.C, callback=self.on_resize)
        ]

        # Run this function once to populate the candle plots on load up
        self.plot_candle_data(None, None, None)

    def _white_theme(self):
        viewport_theme = dcg.ThemeColorImGui(
            self.C,
            border_shadow=(0.960784375667572, 0.960784375667572, 0.960784375667572, 0.0),
            window_bg=(0.9490196704864502, 0.9058824181556702, 0.9058824181556702, 0.9411765336990356),
            title_bg=(0.9803922176361084, 0.9803922176361084, 0.9803922176361084, 1.0),
            text=(0.1, 0.9, 0.14509804546833038, 1.0),
        )
        plot_theme = dcg.ThemeColorImPlot(
            self.C,
            axis_grid=(0.07450980693101883, 0.06666667014360428, 0.06666667014360428, 0.250980406999588),
        )
        theme = dcg.ThemeList(self.C)
        theme.children = [viewport_theme, plot_theme]
        return theme

    def _open_start_date_popup(self, sender, app_data, user_data):
        with dcg.Window(self.C, popup=True, no_title_bar=True, no_resize=True,
                        height=580, width=520) as popup:
            picker = DateTimePicker(
                self.C,
                label="Start Date",
                value=datetime(2024, 8, 5) if getattr(self, "start_date", None) is None else datetime.fromtimestamp(self.start_date),
                use_24hr=False,
                show_seconds=False,
                layout="vertical",
                user_data=popup,
            )
            dcg.Button(
                self.C,
                label="Apply",
                width="fillx",
                callback=self._apply_start_date_time,
                user_data=(popup, picker),
            )

    def _apply_start_date_time(self, sender, app_data, user_data):
        popup, picker = sender.user_data
        self._on_date_picked(picker, picker, picker.value_as_datetime)
        popup.delete_item()

    def _on_date_picked(self, sender, app_data, user_data):
        import calendar
        dt = user_data
        if isinstance(dt, (int, float)):
            dt = datetime.fromtimestamp(dt)
        self.start_date = int(calendar.timegm(dt.timetuple()))
        self.start_date_button.label = dt.strftime("%Y-%m-%d %H:%M")

    def set_status(self, text: str) -> None:
        self.status_text.value = str(text)
        self.C.viewport.wake()

    def on_resize(self, sender, app_data):
        self.status_label.wrap = app_data.width.value - 80

    def plot_candle_data(self, sender, app_data, user_data):
        gap_types = []
        if self.remove_weekends_checkbox.value:
            gap_types.append("weekend")
        if self.remove_overnight_gaps_checkbox.value:
            gap_types.append("overnight")

        start_date = getattr(self, "start_date", None)
        extra = {"start_date": start_date} if start_date is not None else {}

        dates, opens, highs, lows, closes, index, volume = generate_fake_candlestick_data(
            gap_types=gap_types,
            interval=self.interval_radio.value.lower().replace(" ", ""),
            length=500,
            **extra,
        )

        # Update the DearCyFi plot with the generated candle data.
        self.DCF_plot.set_data(
            dates=dates,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            index=index,
            volume=volume,
            time_formatter=lambda x: datetime.fromtimestamp(x).strftime("%b %d"),
        )
        self.DCF_plot.X1.fit()
        self.DCF_plot.Y1.fit()


        orig_dates, orig_opens, orig_highs, orig_lows, orig_closes, _, orig_volume = generate_fake_candlestick_data(
            gap_types=gap_types,
            interval=self.interval_radio.value.lower().replace(" ", ""),
            length=300,
            **extra,
        )

        # Update the original time chart's candlestick plot with the generated candle data.
        if not hasattr(self, "orig_candlestick"):
            # Initialize the original time chart's candlestick plot on first load.
            with self.orig_plot:
                self.orig_candlestick = PlotCandleStick(
                    self.C,
                    dates=orig_dates,
                    opens=orig_opens,
                    closes=orig_closes,
                    lows=orig_lows,
                    highs=orig_highs,
                    label="Stock Price",
                    weight=0.1,
                    time_formatter=lambda x: datetime.fromtimestamp(x).strftime("%b %d"),
                )
        self.orig_candlestick.update_all(
            dates=orig_dates,
            opens=orig_opens,
            closes=orig_closes,
            lows=orig_lows,
            highs=orig_highs,
            volumes=orig_volume,
        )
        self.orig_plot.X1.fit()
        self.orig_plot.Y1.fit()


        self.set_status("Loaded fresh candle data into DearCyFi.")


if __name__ == "__main__":
    app = DearCyFiDemo(white_theme=False)
    try:
        loop.run_until_complete(run_viewport_loop(app.C.viewport))
    except KeyboardInterrupt:
        print("Got the strange window close keyboard interrupt bug. Exiting DearCyFi demo.")
    finally:
        # Cancel any lingering async tasks so the loop can shut down cleanly.
        for task in asyncio.all_tasks(loop):
            task.cancel()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        print("DearCyFi demo closed.")
