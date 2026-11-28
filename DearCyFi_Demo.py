"""DearCyFi demo GUI.

Usage notes:
- Host apps feed fresh candle arrays into `DearCyFi` via `set_data(...)`.
- Time-collapse actions are invoked on the plot object (`collapse_time_chart`,
  `collapse_time_chart_vec`) instead of host-managed gap/locator objects.

New shared string stuffs:

# In your overlay window with a semi-transparent theme:
dcg.Text(self.C, shareable_value=self.DCF_plot.debug_text, wrap=400)

test
"""

import asyncio
import importlib
from datetime import datetime

import dearcygui as dcg
import numpy as np
from dearcygui.utils.asyncio_helpers import AsyncPoolExecutor, run_viewport_loop

from demo_widgets import DateTimePicker
from data_widgets import DATA_WIDGETS
from toy_data_browser import ToyDataBrowser
from synthetic_candle_stream import SyntheticCandleStream

from dearcyfi import DearCyFi, PlotEconometricSeries
from dearcyfi.candle_utils.candle_gen import generate_fake_candlestick_data

from dearcyfi.DCG_Candle_Utils import PlotCandleStick

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


class DearCyFiDemo:
    def __init__(self, white_theme: bool = False):
        self._stream_task = None
        self._stream_shutdown_task = None
        self._reload_task = None
        self._stream_gap_next = False
        self.C = dcg.Context()
        self._legend_test_series = {}
        self._indicator_edit_popups = {}
        self.C.queue = AsyncPoolExecutor()
        self.C.viewport.wait_for_input = True

        if white_theme:
            self.C.viewport.initialize(height=900, width=1600, theme=self._white_theme())
        else:
            self.C.viewport.initialize(height=900, width=1600)

        with dcg.Window(self.C, label="DearCyFi Demo", primary=True, width="fillx", height="filly") as main_window:
            with dcg.HorizontalLayout(self.C, no_wrap=True):
                with dcg.ChildWindow(self.C, label="Left Side", width=320, resizable_x=True) as self.left_win:

                    # Under the plot candle data button we want to add some controls that will allow us to:
                    # 1. remove or not remove weekends from the time series
                    # 2. remove or not remove overnight gaps from the time series (from 4pm to 9:30am the next day)
                    # 3. change between weekly, daily, hourly, 15 minutes, and 5 minute data intervals
                    # This will be accomplished with a combination of checkboxes and radiobuttons
                    # We will want to have some kind of layout for these controls that makes them look nice and organized under the plot candle data button
                    with dcg.CollapsingHeader(self.C, label="Fake Candle Controls",value=False):
                        self.plot_button = dcg.Button(
                            self.C,
                            label="Reload Candle Data",
                            width="fillx",
                            height='main_window.height/24+10', #32
                            callback=self.plot_candle_data,
                        )
                        self.load_bars_button = dcg.Button(
                            self.C,
                            label="Load Bar Data",
                            width="fillx",
                            height='main_window.height/24+10',
                            callback=lambda s, a, u: self.DCF_plot.load_horizontal_bars(
                                s,
                                a,
                                u,
                                value_space=self.bar_length_mode.value.lower(),
                            ),
                        )
                        dcg.Text(self.C, value="Bar Length Mode:")
                        self.bar_length_mode = dcg.RadioButton(
                            self.C,
                            items=["Data", "Normalized"],
                            value="Data",
                        )
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
                                        value="Daily",  #set default data interval for synthetic data
                                    )
                                    dcg.Text(self.C, value="Candle Count:")
                                    self.candle_count_slider = dcg.Slider(
                                        self.C,
                                        min_value=10,
                                        max_value=5000,
                                        value=50,
                                        width="fillx",
                                        print_format="%.0f",
                                    )
                                    dcg.Text(self.C, value="Start Date:")
                                    self.start_date_button = dcg.Button(
                                        self.C,
                                        label="Start Date",
                                        width="fillx",
                                        callback=self._open_start_date_popup,
                                    )
                                    dcg.Text(self.C, value="Synthetic stream update period (seconds):")
                                    self.stream_period_slider = dcg.Slider(
                                        self.C,
                                        min_value=0.1,
                                        max_value=5.0,
                                        value=0.5,
                                        width="fillx",
                                        print_format="%.1f",
                                    )
                                    self.stream_gap_checkbox = dcg.Checkbox(
                                        self.C,
                                        label="Gap next appended candle",
                                        callback=self._set_stream_gap_next,
                                    )
                                    self.start_stream_button = dcg.Button(
                                        self.C,
                                        label="Start Synthetic Stream",
                                        width="fillx",
                                        callback=self._start_candle_stream,
                                    )
                                    self.stop_stream_button = dcg.Button(
                                        self.C,
                                        label="Stop Synthetic Stream",
                                        width="fillx",
                                        callback=self._stop_candle_stream,
                                    )
                                    self.stream_status = dcg.Text(self.C, value="Stream stopped.")

                    # =========================
                    # TOY DATA TREE PLACEHOLDER
                    # Replace this UI with DB-backed symbol browser controls.
                    # =========================
                    with dcg.CollapsingHeader(self.C, label="Data Tree",value=False):
                        self.toy_data_browser = ToyDataBrowser(
                            self.C,
                            label="Toy Data Tree",
                            width="fillx",
                            height=260,
                            on_symbol_selected=self._on_toy_symbol_selected,
                        )

                    with dcg.CollapsingHeader(self.C, label="Econometric Data", value=True):
                        econometric_factory = DATA_WIDGETS.get("toy-econometric")
                        self.econometric_widget = econometric_factory(
                            self.C,
                            label="Toy Econometric Provider",
                            width="fillx",
                            height=150,
                            on_load_requested=self._on_data_load_requested,
                            on_status=self.set_status,
                        )

                    with dcg.CollapsingHeader(self.C, label="Candle Indicators", value=True):
                        dcg.Text(self.C, value="Indicator type:")
                        self.indicator_type_radio = dcg.RadioButton(
                            self.C,
                            items=["SMA"],
                            value="SMA",
                        )
                        dcg.Text(self.C, value="SMA period:")
                        self.indicator_period_slider = dcg.Slider(
                            self.C,
                            min_value=1,
                            max_value=500,
                            value=20,
                            width="fillx",
                            print_format="%.0f",
                        )
                        dcg.Text(self.C, value="OHLC field:")
                        self.indicator_field_radio = dcg.RadioButton(
                            self.C,
                            items=["Open", "High", "Low", "Close"],
                            value="Close",
                        )
                        dcg.Text(self.C, value="Line color:")
                        self.indicator_line_color_edit = dcg.ColorEdit(
                            self.C,
                            value=(255, 196, 0, 255),
                            width="fillx",
                        )
                        self.add_indicator_button = dcg.Button(
                            self.C,
                            label="Add",
                            width="fillx",
                            callback=self._add_sma_indicator,
                        )
                        self.indicator_status = dcg.Text(
                            self.C,
                            value="No candle indicators.",
                            wrap=300,
                        )

                    with dcg.CollapsingHeader(self.C, label="Technical Analysis", value=False):
                        self.add_box_button = dcg.Button(
                            self.C,
                            label="Add Box",
                            width="fillx",
                            height='main_window.height/24+10',
                            callback=self._add_box,
                        )
                        self.print_boxes_button = dcg.Button(
                            self.C,
                            label="Print Boxes",
                            width="fillx",
                            height='main_window.height/24+10',
                            callback=self._print_boxes,
                        )
                        self.remove_boxes_button = dcg.Button(
                            self.C,
                            label="Remove All Boxes",
                            width="fillx",
                            height='main_window.height/24+10',
                            callback=self._remove_all_boxes,
                        )

                    with dcg.CollapsingHeader(self.C, label="Status Text",value=False):
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
                                on_chart_restored=self._on_chart_restored,
                                apply_date_context_labels=False,
                            )
                            self.DCF_plot.Y3.enabled = True
                            self.DCF_plot.Y3.label = "Econometric Value"

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
        self._on_data_load_requested(
            self.econometric_widget,
            self.econometric_widget.build_request(),
        )

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

    def _on_toy_symbol_selected(self, widget, symbol, profile):
        self.plot_candle_data(None, None, None)

    def _set_stream_gap_next(self, sender, app_data, user_data):
        self._stream_gap_next = bool(sender.value)
        feed = getattr(self, "_stream_feed", None)
        if feed is not None:
            feed.gap_next = self._stream_gap_next

    def _start_candle_stream(self, sender=None, app_data=None, user_data=None):
        if self._stream_task is not None and not self._stream_task.done():
            self.stream_status.value = "Stream already running."
            return
        if (
            self._stream_shutdown_task is not None
            and not self._stream_shutdown_task.done()
        ) or (self._reload_task is not None and not self._reload_task.done()):
            self.stream_status.value = "Wait for the previous stream to stop."
            return
        try:
            dates = np.asarray(self.DCF_plot.candlestick_plot.source_dates, dtype=float)
            if dates.size < 2:
                raise ValueError("Load at least two candles before starting the stream.")
            cadence = float(np.median(np.diff(dates)))
            if not np.isfinite(cadence) or cadence <= 0:
                raise ValueError("Loaded candle history does not have a valid interval.")
        except Exception as exc:
            self.stream_status.value = f"Stream error: {exc}"
            self.set_status(self.stream_status.value)
            return

        profile = self.toy_data_browser.get_selected_profile()
        symbol_seed = sum(ord(character) for character in self.toy_data_browser.selected_symbol)
        feed = SyntheticCandleStream(cadence, int(profile["seed"]) + symbol_seed)
        feed.gap_next = self._stream_gap_next
        self._stream_feed = feed
        self._stream_task = loop.create_task(
            self._run_candle_stream(cadence, feed),
        )
        self.stream_status.value = f"Stream running ({cadence:g}s loaded interval)."
        self.set_status(self.stream_status.value)

    def _stop_candle_stream(self, sender=None, app_data=None, user_data=None):
        task = self._stream_task
        if task is not None and not task.done():
            task.cancel()
        self._stream_task = None
        self._stream_feed = None
        if task is not None and not task.done():
            self._stream_shutdown_task = loop.create_task(self._await_stream_stop(task))
        if hasattr(self, "stream_status"):
            self.stream_status.value = "Stream stopped."
            self.set_status("Synthetic candle stream stopped.")

    async def _await_stream_stop(self, task):
        await asyncio.gather(task, return_exceptions=True)
        if hasattr(self, "stream_status"):
            self.stream_status.value = "Stream stopped."

    async def _reload_after_stream_stop(self, task, sender, app_data, user_data):
        await asyncio.gather(task, return_exceptions=True)
        self._load_candle_data(sender, app_data, user_data)

    async def _reload_after_stop_wait(self, sender, app_data, user_data):
        task = self._stream_shutdown_task
        if task is not None:
            await asyncio.gather(task, return_exceptions=True)
        self._load_candle_data(sender, app_data, user_data)

    async def _shutdown_stream(self):
        task = self._stream_task
        self._stream_task = None
        self._stream_feed = None
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        pending = [
            pending_task
            for pending_task in (self._stream_shutdown_task, self._reload_task)
            if pending_task is not None and not pending_task.done()
        ]
        for pending_task in pending:
            pending_task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

    async def _run_candle_stream(self, cadence: float, feed: SyntheticCandleStream):
        current_task = asyncio.current_task()
        try:
            while True:
                await asyncio.sleep(float(self.stream_period_slider.value))
                if self._stream_task is not current_task:
                    return

                candle = self.DCF_plot.candlestick_plot
                source_dates = np.asarray(candle.source_dates, dtype=float)
                latest_timestamp = float(source_dates[-1])
                event_type, event_timestamp, values = feed.next_event(
                    timestamp=latest_timestamp,
                    high=float(candle.highs[-1]),
                    low=float(candle.lows[-1]),
                    close=float(candle.closes[-1]),
                    volume=float(candle.volumes[-1]),
                )
                if event_type == "update":
                    match, _ = self.DCF_plot.check_last_candle(event_timestamp + cadence * 0.5)
                    if not match:
                        raise RuntimeError("Generated revision no longer occupies the latest candle interval.")
                    self.DCF_plot.update_last_candle(**values)
                else:
                    self.DCF_plot.append_candle(
                        timestamp=event_timestamp,
                        **values,
                    )
                    self._stream_gap_next = False
                    self.stream_gap_checkbox.value = False

                candle = self.DCF_plot.candlestick_plot
                self.orig_candlestick.update_all(
                    dates=np.asarray(candle.source_dates, dtype=float),
                    source_dates=np.asarray(candle.source_dates, dtype=float),
                    opens=np.asarray(candle.opens, dtype=float),
                    closes=np.asarray(candle.closes, dtype=float),
                    lows=np.asarray(candle.lows, dtype=float),
                    highs=np.asarray(candle.highs, dtype=float),
                    volumes=np.asarray(candle.volumes, dtype=float),
                )
                self.C.viewport.wake(full_refresh=True)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self._stream_task = None
            self._stream_feed = None
            self.stream_status.value = f"Stream error: {exc}"
            self.set_status(self.stream_status.value)
        else:
            self._stream_task = None
            self._stream_feed = None
            self.stream_status.value = "Stream stopped."

    def _on_data_load_requested(self, widget, request):
        result = widget.load(request)
        line_series = next((series for series in result.series if series.kind == "line"), None)
        if line_series is None:
            raise ValueError("The toy econometric provider did not return a line series")

        dates = line_series.timestamps
        values = line_series.values["value"]
        if getattr(self, "econometric_series", None) is None:
            with self.DCF_plot:
                self.econometric_series = PlotEconometricSeries(
                    self.C,
                    dates=dates,
                    values=values,
                    label=line_series.name,
                    markers=True,
                    y_axis=dcg.Axis.Y3,
                )
            self.DCF_plot.Y3.enabled = True
        else:
            self.econometric_series.update_all(
                dates=dates,
                values=values,
                label=line_series.name,
            )

        self.DCF_plot.register_time_series(
            "toy-econometric",
            self.econometric_series,
            in_gap="next",
            replace="toy-econometric" in self.DCF_plot.time_series_ids,
        )
        self._attach_legend_test_menu(self.econometric_series)
        getattr(self.DCF_plot, self.econometric_series.y_axis.name).fit()
        self.set_status(
            f"Loaded {result.display_name}; collapse source remains "
            f"{self.DCF_plot.collapse_source_id!r}."
        )

    def _on_chart_restored(self, chart):
        # This runs on the same callback loop as the stream and provider reloads.
        if self._reload_task is not None and not self._reload_task.done():
            self._reload_task.cancel()
        self._stop_candle_stream()
        self._stream_gap_next = False
        self.stream_gap_checkbox.value = False
        for popup in self._indicator_edit_popups.values():
            popup.delete_item()
        self._indicator_edit_popups.clear()
        self._legend_test_series = {
            key: identity for key, identity in self._legend_test_series.items()
            if identity.parent is not None
        }
        self.econometric_series = (
            chart.get_time_series("toy-econometric") if "toy-econometric" in chart.time_series_ids else None
        )
        for item_id in chart.time_series_ids:
            self._attach_legend_test_menu(chart.get_time_series(item_id))
        for instance in chart.indicator_instances.values():
            self._attach_indicator_menu(instance.series)
        self.indicator_status.value = f"Restored {len(chart.indicator_ids)} indicator(s)."

    def _attach_legend_test_menu(self, series):
        if series.uuid in self._legend_test_series:
            self._legend_test_series[series.uuid].value = f"Series: {series.label} (ID {series.uuid})"
            return
        with series:
            identity = dcg.Text(self.C, value=f"Series: {series.label} (ID {series.uuid})", wrap=300)
            result = dcg.Text(self.C, value="No action for this series yet.", wrap=300)
            dcg.Button(
                self.C,
                label="Identify this series",
                callback=self._identify_legend_series,
                user_data=result,
            )
        self._legend_test_series[series.uuid] = identity

    def _add_sma_indicator(self, sender, app_data, user_data):
        try:
            period = int(round(float(self.indicator_period_slider.value)))
            field = str(self.indicator_field_radio.value).lower()
            instance = self.DCF_plot.create_indicator(
                type="SMA",
                period=period,
                field=field,
                y_axis=dcg.Axis.Y1,
                line_color=dcg.color_as_ints(self.indicator_line_color_edit.value),
            )
        except Exception as exc:
            self.indicator_status.value = f"Could not add SMA: {exc}"
            self.set_status(self.indicator_status.value)
            return
        self._attach_legend_test_menu(instance.series)
        self._attach_indicator_menu(instance.series)
        self.indicator_status.value = (
            f"Added {instance.calculator.name} "
            f"(ID {instance.instance_id})."
        )
        self.set_status(self.indicator_status.value)

    def _attach_indicator_menu(self, series):
        existing = [
            child for child in series.children
            if isinstance(child, dcg.Button)
            and getattr(child, "label", None) in ("Edit indicator", "Remove indicator")
        ]
        if existing:
            for child in existing:
                child.user_data = series.indicator_id
            return
        with series:
            dcg.Button(
                self.C,
                label="Edit indicator",
                callback=self._open_indicator_edit_popup,
                user_data=series.indicator_id,
            )
            dcg.Button(
                self.C,
                label="Remove indicator",
                callback=self._remove_indicator,
                user_data=series.indicator_id,
            )

    def _open_indicator_edit_popup(self, sender):
        instance_id = sender.user_data
        try:
            instance = self.DCF_plot.indicator_manager.get(instance_id)
        except Exception as exc:
            self.set_status(str(exc))
            return
        if sender.parent is not instance.series:
            return
        popup = self._indicator_edit_popups.get(instance_id)
        if popup is not None:
            popup.focus()
            return
        parameters = instance.calculator.parameters
        with dcg.Window(
            self.C,
            label=f"Edit {instance.calculator.name}",
            popup=True,
            no_resize=True,
            no_collapse=True,
            width=300,
            height=280,
        ) as popup:
            dcg.Text(self.C, value="SMA period:")
            period_slider = dcg.Slider(
                self.C,
                min_value=1,
                max_value=500,
                value=int(parameters["period"]),
                width="fillx",
                print_format="%.0f",
            )
            dcg.Text(self.C, value="OHLC field:")
            field_radio = dcg.RadioButton(
                self.C,
                items=["Open", "High", "Low", "Close"],
                value=str(parameters["field"]).title(),
            )
            dcg.Text(self.C, value="Line color:")
            line_color_edit = dcg.ColorEdit(
                self.C,
                value=instance.series.line_color,
                width="fillx",
            )
            error_text = dcg.Text(self.C, value="")
            dcg.Button(
                self.C,
                label="Apply",
                width="fillx",
                callback=self._apply_indicator_edit,
                user_data=(
                    instance_id,
                    popup,
                    period_slider,
                    field_radio,
                    line_color_edit,
                    error_text,
                ),
            )
            dcg.Button(
                self.C,
                label="Cancel",
                width="fillx",
                callback=self._cancel_indicator_edit,
                user_data=(instance_id, popup),
            )
        self._indicator_edit_popups[instance_id] = popup

    def _apply_indicator_edit(self, sender):
        (
            instance_id,
            popup,
            period_slider,
            field_radio,
            line_color_edit,
            error_text,
        ) = sender.user_data
        if self._indicator_edit_popups.get(instance_id) is not popup:
            return
        try:
            period = int(round(float(period_slider.value)))
            field = str(field_radio.value).lower()
            instance = self.DCF_plot.edit_indicator(
                instance_id,
                period=period,
                field=field,
                line_color=dcg.color_as_ints(line_color_edit.value),
            )
        except Exception as exc:
            error_text.value = str(exc)
            self.set_status(str(exc))
            return
        popup.delete_item()
        self._indicator_edit_popups.pop(instance_id, None)
        self._attach_legend_test_menu(instance.series)
        self._attach_indicator_menu(instance.series)
        message = f"Updated indicator {instance.instance_id}: {instance.calculator.name}"
        self.indicator_status.value = message
        self.set_status(message)

    def _cancel_indicator_edit(self, sender):
        instance_id, popup = sender.user_data
        if self._indicator_edit_popups.get(instance_id) is not popup:
            return
        popup.delete_item()
        self._indicator_edit_popups.pop(instance_id, None)
        self.set_status("Indicator edit canceled.")

    def _remove_indicator(self, sender):
        instance_id = sender.user_data
        try:
            instance = self.DCF_plot.indicator_manager.get(instance_id)
            if sender.parent is not instance.series:
                return
            self.DCF_plot.remove_indicator(instance_id)
        except Exception as exc:
            self.indicator_status.value = f"Could not remove indicator: {exc}"
            self.set_status(self.indicator_status.value)
            return
        popup = self._indicator_edit_popups.pop(instance_id, None)
        if popup is not None:
            popup.delete_item()
        self._legend_test_series.pop(instance.series.uuid, None)
        self.indicator_status.value = f"Removed indicator {instance_id}."
        self.set_status(self.indicator_status.value)

    def _identify_legend_series(self, sender, app_data, user_data):
        series = sender.parent
        plot = series.parent if series is not None else None
        if plot is None:
            return
        message = f"Legend action: {plot.label} / {series.label} (ID {series.uuid})"
        sender.user_data.value = message
        self.set_status(message)

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

        #print the picked date as a timestamp and as a datetime for debugging
        print(f"Picked start date: {self.start_date} (timestamp), {dt} (datetime)")

    def set_status(self, text: str) -> None:
        self.status_text.value = str(text)
        self.C.viewport.wake()

    def _add_box(self, sender=None, app_data=None, user_data=None):
        box = self.DCF_plot.add_box()
        self.set_status(f"Added {box.tool_id}.")

    def _print_boxes(self, sender=None, app_data=None, user_data=None):
        self.set_status(self.DCF_plot.print_boxes())

    def _remove_all_boxes(self, sender=None, app_data=None, user_data=None):
        existing_count = len(self.DCF_plot.boxes)
        self.DCF_plot.remove_all_boxes()
        if existing_count == 0:
            self.set_status("No range boxes.")
        elif existing_count == 1:
            self.set_status("Removed 1 range box.")
        else:
            self.set_status(f"Removed {existing_count} range boxes.")

    def on_resize(self, sender, app_data):
        self.status_label.wrap = app_data.width.value - 80

    def plot_candle_data(self, sender, app_data, user_data):
        if self._reload_task is not None and not self._reload_task.done():
            return
        task = self._stream_task
        if task is not None and not task.done():
            self._stream_task = None
            self._stream_feed = None
            task.cancel()
            self._reload_task = loop.create_task(
                self._reload_after_stream_stop(task, sender, app_data, user_data)
            )
            return
        if (
            self._stream_shutdown_task is not None
            and not self._stream_shutdown_task.done()
        ):
            self._reload_task = loop.create_task(
                self._reload_after_stop_wait(sender, app_data, user_data)
            )
            return
        self._load_candle_data(sender, app_data, user_data)

    def _load_candle_data(self, sender, app_data, user_data):
        gap_types = []
        if self.remove_weekends_checkbox.value:
            gap_types.append("weekend")
        if self.remove_overnight_gaps_checkbox.value:
            gap_types.append("overnight")
        candle_count = int(self.candle_count_slider.value)

        # TOY PROFILE PLACEHOLDER:
        # Swap this for live series config loaded from your database.
        toy_profile = self.toy_data_browser.get_selected_profile()
        selected_symbol = self.toy_data_browser.selected_symbol

        start_date = getattr(self, "start_date", None)
        generator_kwargs = {
            "base_price": toy_profile["base_price"],
            "volatility": toy_profile["volatility"],
            "seed": toy_profile["seed"],
            "start_date": start_date if start_date is not None else toy_profile["start_date"],
        }

        dates, opens, highs, lows, closes, index, volume = generate_fake_candlestick_data(
            gap_types=gap_types,
            interval=self.interval_radio.value.lower().replace(" ", ""),
            length=candle_count,
            **generator_kwargs,
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
            time_formatter="auto",
            candle_y_axis=dcg.Axis.Y1,
        )
        self._attach_legend_test_menu(self.DCF_plot.candlestick_plot)
        self.DCF_plot.X1.fit()
        self.DCF_plot.Y1.fit()


        orig_dates, orig_opens, orig_highs, orig_lows, orig_closes, _, orig_volume = generate_fake_candlestick_data(
            gap_types=gap_types,
            interval=self.interval_radio.value.lower().replace(" ", ""),
            length=candle_count,
            **generator_kwargs,
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
                    time_formatter="auto",
                )
        self.orig_candlestick.update_all(
            dates=orig_dates,
            opens=orig_opens,
            closes=orig_closes,
            lows=orig_lows,
            highs=orig_highs,
            volumes=orig_volume,
        )
        self._attach_legend_test_menu(self.orig_candlestick)
        self.orig_plot.X1.fit()
        self.orig_plot.Y1.fit()


        self.set_status(f"Loaded fresh candle data for toy symbol {selected_symbol}.")


if __name__ == "__main__":
    app = DearCyFiDemo(white_theme=False)
    try:
        loop.run_until_complete(run_viewport_loop(app.C.viewport))
    except KeyboardInterrupt:
        print("Got the strange window close keyboard interrupt bug. Exiting DearCyFi demo.")
    finally:
        # Cancel any lingering async tasks so the loop can shut down cleanly.
        loop.run_until_complete(app._shutdown_stream())
        for task in asyncio.all_tasks(loop):
            task.cancel()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        print("DearCyFi demo closed.")
