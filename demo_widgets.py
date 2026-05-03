"""Local demo widgets copied from DearCyGui for project-specific customization."""

from __future__ import annotations

import colorsys
from datetime import datetime
import typing

import dearcygui as dcg


class TimePicker(dcg.Layout):
    """A local copy of DearCyGui's TimePicker for demo-specific customization."""

    def __init__(self, context, *, value=None, use_24hr=False, show_seconds=True, **kwargs) -> None:
        super().__init__(context, **kwargs)

        if value is None:
            value = datetime.now()
        if isinstance(value, datetime):
            total_seconds = value.hour * 3600 + value.minute * 60 + value.second
        else:
            total_seconds = float(value)

        self._value = dcg.SharedFloat(context, total_seconds)
        self._use_24hr = use_24hr
        self._show_seconds = show_seconds

        self.border = True
        self.no_scrollbar = True
        self.no_scroll_with_mouse = True
        with dcg.ThemeList(self.context) as self.theme:
            self._container_style = dcg.ThemeStyleImGui(
                self.context,
                frame_rounding=4.0,
                child_rounding=4.0,
                frame_padding=(6, 3),
                item_spacing=(4, 4),
            )
            self._container_colors = dcg.ThemeColorImGui(self.context)
        self._input_colors = dcg.ThemeColorImGui(context)
        self._separator_colors = dcg.ThemeColorImGui(context)
        self._ampm_colors = dcg.ThemeColorImGui(context)

        self.handlers += [
            dcg.GotRenderHandler(context, callback=self._update_theme_style)
        ]

        with dcg.HorizontalLayout(context, parent=self):
            dcg.Text(context, value="hrs :", width=10, theme=self._separator_colors)
            self._hours = dcg.InputValue(
                context,
                print_format="%.0f",
                min_value=0,
                max_value=23 if use_24hr else 12,
                value=self._get_display_hour(),
                width=100,
                step=1,
                step_fast=5,
                callback=self._on_hour_change,
            )
            self._hours.theme = self._input_colors

            dcg.Text(context, value="mins :", width=10, theme=self._separator_colors)
            self._minutes = dcg.InputValue(
                context,
                print_format="%.0f",
                min_value=0,
                max_value=59,
                value=int((total_seconds % 3600) // 60),
                width=100,
                step=1,
                step_fast=5,
                callback=self._on_minute_change,
            )
            self._minutes.theme = self._input_colors

            if show_seconds:
                dcg.Text(context, value="secs :", width=10, theme=self._separator_colors)
                self._seconds = dcg.InputValue(
                    context,
                    print_format="%.0f",
                    min_value=0,
                    max_value=59,
                    value=int(total_seconds % 60),
                    width=100,
                    step=1,
                    step_fast=5,
                    callback=self._on_second_change,
                )
                self._seconds.theme = self._input_colors

            if not use_24hr:
                dcg.Text(context, value=" ", width=10)
                self._am_pm = dcg.RadioButton(
                    context,
                    items=["AM", "PM"],
                    value="PM" if (total_seconds // 3600) >= 12 else "AM",
                    horizontal=True,
                    callback=self._on_ampm_change,
                )
                self._am_pm.theme = self._ampm_colors

    def _update_theme_style(self) -> None:
        parent = self.parent
        assert parent is not None
        text_color = typing.cast(int, dcg.resolve_theme(parent, dcg.ThemeColorImGui, "text"))
        frame_bg = typing.cast(int, dcg.resolve_theme(parent, dcg.ThemeColorImGui, "frame_bg"))
        frame_bg_hovered = typing.cast(int, dcg.resolve_theme(parent, dcg.ThemeColorImGui, "frame_bg_hovered"))
        frame_bg_active = typing.cast(int, dcg.resolve_theme(parent, dcg.ThemeColorImGui, "frame_bg_active"))
        child_bg = typing.cast(int, dcg.resolve_theme(parent, dcg.ThemeColorImGui, "child_bg"))

        accent_color = dcg.resolve_theme(parent, dcg.ThemeColorImGui, "check_mark")
        accent_color = dcg.color_as_floats(accent_color)
        if sum(accent_color[:3]) < 0.1:
            accent_color = (0.4, 0.5, 0.8, 0.7)

        self._container_colors.text = text_color
        self._container_colors.child_bg = child_bg

        self._input_colors.text = text_color
        self._input_colors.frame_bg = frame_bg
        self._input_colors.frame_bg_hovered = frame_bg_hovered
        self._input_colors.frame_bg_active = frame_bg_active
        text_color = dcg.color_as_floats(text_color)
        frame_bg = dcg.color_as_floats(frame_bg)
        frame_bg_hovered = dcg.color_as_floats(frame_bg_hovered)
        frame_bg_active = dcg.color_as_floats(frame_bg_active)

        self._separator_colors.text = tuple(
            0.3 * text_color[index] + 0.7 * accent_color[index]
            for index in range(3)
        ) + (text_color[3],)

        self._ampm_colors.frame_bg = tuple(channel * 0.95 for channel in frame_bg[:3]) + (frame_bg[3],)
        self._ampm_colors.frame_bg_hovered = tuple(min(1.0, channel * 1.05) for channel in frame_bg_hovered[:3]) + (frame_bg_hovered[3],)
        self._ampm_colors.frame_bg_active = tuple(channel * 0.9 for channel in frame_bg_active[:3]) + (frame_bg_active[3],)
        self._ampm_colors.text = text_color

    def _get_display_hour(self) -> int:
        hour = int(self._value.value // 3600)
        if not self._use_24hr:
            hour = hour % 12
            if hour == 0:
                hour = 12
        return hour

    def _get_total_seconds(self, hour: int, minute: int, second: int | None = None) -> int:
        if second is None:
            second = int(self._value.value % 60)
        return hour * 3600 + minute * 60 + second

    def _on_hour_change(self, sender, target, value) -> None:
        hour = int(value)
        if not self._use_24hr:
            is_pm = self._am_pm.value == "PM"
            if hour == 12:
                hour = 0 if not is_pm else 12
            elif is_pm:
                hour += 12

        minute = int((self._value.value % 3600) // 60)
        self._value.value = self._get_total_seconds(hour, minute)
        self.run_callbacks()

    def _on_minute_change(self, sender, target, value) -> None:
        hour = int(self._value.value // 3600)
        self._value.value = self._get_total_seconds(hour, int(value))
        self.run_callbacks()

    def _on_second_change(self, sender, target, value) -> None:
        if self._show_seconds:
            hour = int(self._value.value // 3600)
            minute = int((self._value.value % 3600) // 60)
            self._value.value = self._get_total_seconds(hour, minute, int(value))
            self.run_callbacks()

    def _on_ampm_change(self, sender, target, value) -> None:
        if not self._use_24hr:
            hour = int(self._value.value // 3600)
            current_is_pm = hour >= 12
            new_is_pm = value == "PM"

            if current_is_pm != new_is_pm:
                hour = (hour + 12) % 24
                minute = int((self._value.value % 3600) // 60)
                self._value.value = self._get_total_seconds(hour, minute)
                self.run_callbacks()

    def run_callbacks(self) -> None:
        for callback in self.callbacks:
            callback(self, self, self.value_as_datetime)

    @property
    def value(self) -> float:
        return self._value.value

    @value.setter
    def value(self, value: float | datetime) -> None:
        if isinstance(value, datetime):
            value = value.hour * 3600 + value.minute * 60 + value.second
        self._value.value = float(value)

        self._hours.value = self._get_display_hour()
        self._minutes.value = int((self._value.value % 3600) // 60)
        if self._show_seconds:
            self._seconds.value = int(self._value.value % 60)
        if not self._use_24hr:
            self._am_pm.value = "PM" if (self._value.value // 3600) >= 12 else "AM"

    @property
    def value_as_datetime(self) -> datetime:
        total_seconds = int(self._value.value)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return datetime.now().replace(hour=hours, minute=minutes, second=seconds)

    @value_as_datetime.setter
    def value_as_datetime(self, value) -> None:
        if not isinstance(value, datetime):
            raise ValueError("Value must be a datetime object")
        self.value = value

    @property
    def use_24hr(self) -> bool:
        return self._use_24hr

    @use_24hr.setter
    def use_24hr(self, value: bool) -> None:
        if value != self._use_24hr:
            self._use_24hr = value
            self._hours.max_value = 23 if value else 12
            self._hours.value = self._get_display_hour()
            if hasattr(self, "_am_pm"):
                self._am_pm.show = not value

    @property
    def show_seconds(self) -> bool:
        return self._show_seconds

    @show_seconds.setter
    def show_seconds(self, value: bool) -> None:
        if value != self._show_seconds:
            self._show_seconds = value
            if hasattr(self, "_seconds"):
                self._seconds.show = value


class DatePicker(dcg.ChildWindow):
    """A local copy of DearCyGui's DatePicker for demo-specific customization."""

    MONTH_NAMES = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]

    MONTH_ABBREV = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]

    WEEKDAY_ABBREV = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]

    def __init__(self, context, *, value=None, min_date=None, max_date=None, **kwargs):
        super().__init__(context, **kwargs)

        self._value = dcg.SharedFloat(context, 0)
        self._view_level = 0  # 0=days, 1=months, 2=years

        if value is None:
            value = datetime.now()
        if not isinstance(value, datetime):
            raise ValueError("Value must be a datetime object")

        self._min_date = datetime(1970, 1, 1) if min_date is None else min_date
        self._max_date = datetime(2999, 12, 31) if max_date is None else max_date

        self._value.value = value.timestamp()
        self._current_month = value.month - 1
        self._current_year = value.year
        self._current_year_block = value.year - (value.year % 20)

        self.border = True
        self.auto_resize_y = True
        self.no_scrollbar = True
        self.no_scroll_with_mouse = True
        self._container_style = dcg.ThemeStyleImGui(
            context,
            frame_rounding=4.0,
            frame_padding=(6, 3),
            child_rounding=4.0,
            item_spacing=(8, 4),
        )
        self._container_colors = dcg.ThemeColorImGui(context)
        self.theme = dcg.ThemeList(context)
        self._container_style.parent = self.theme
        self._container_colors.parent = self.theme

        self._nav_button_colors = dcg.ThemeColorImGui(context)
        self._header_button_colors = dcg.ThemeColorImGui(context)
        self._weekday_header_colors = dcg.ThemeColorImGui(context)
        self._day_button_colors = dcg.ThemeColorImGui(context)
        self._selected_day_colors = dcg.ThemeColorImGui(context)
        self._today_day_colors = dcg.ThemeColorImGui(context)
        self._disabled_day_colors = dcg.ThemeColorImGui(context)

        self.handlers += [
            dcg.GotRenderHandler(context, callback=self._update_theme_style)
        ]

        with self:
            with dcg.HorizontalLayout(context):
                self._left_btn = dcg.Button(
                    context,
                    label="<",
                    width=30,
                    callback=self._on_prev_click,
                )
                self._left_btn.theme = self._nav_button_colors

                self._header_btn = dcg.Button(
                    context,
                    label=self._get_header_text(),
                    width=170,
                    callback=self._on_header_click,
                )
                self._header_btn.theme = self._header_button_colors

                self._right_btn = dcg.Button(
                    context,
                    label=">",
                    width=30,
                    callback=self._on_next_click,
                )
                self._right_btn.theme = self._nav_button_colors

            self._grid = dcg.Layout(context)
            self._update_grid()

    def _update_theme_style(self) -> None:
        parent = self.parent
        assert parent is not None
        text_color = typing.cast(int, dcg.resolve_theme(parent, dcg.ThemeColorImGui, "text"))
        button_color = typing.cast(int, dcg.resolve_theme(parent, dcg.ThemeColorImGui, "button"))
        button_hovered = typing.cast(int, dcg.resolve_theme(parent, dcg.ThemeColorImGui, "button_hovered"))
        button_active = typing.cast(int, dcg.resolve_theme(parent, dcg.ThemeColorImGui, "button_active"))
        child_bg = typing.cast(int, dcg.resolve_theme(parent, dcg.ThemeColorImGui, "child_bg"))
        border_color = typing.cast(int, dcg.resolve_theme(parent, dcg.ThemeColorImGui, "border"))

        accent_color = dcg.resolve_theme(parent, dcg.ThemeColorImGui, "check_mark")
        accent_color = dcg.color_as_floats(accent_color)
        if sum(accent_color[:3]) < 0.1:
            accent_color = (0.4, 0.5, 0.8, 0.7)

        h, s, v = colorsys.rgb_to_hsv(*accent_color[:3])
        h = (h + 0.5) % 1.0
        today_color = colorsys.hsv_to_rgb(h, s * 0.8, v)
        today_color = today_color[:3] + (0.7,)

        text_color = dcg.color_as_floats(text_color)

        self._container_colors.text = text_color
        self._container_colors.button = button_color
        self._container_colors.child_bg = child_bg
        self._container_colors.border = border_color

        self._nav_button_colors.button = button_color
        self._nav_button_colors.button_hovered = button_hovered
        self._nav_button_colors.button_active = button_active
        self._nav_button_colors.text = text_color

        button_color = dcg.color_as_floats(button_color)
        header_bg = tuple(min(1.0, channel * 1.1) for channel in button_color[:3]) + (button_color[3],)
        self._header_button_colors.button = header_bg
        self._header_button_colors.button_hovered = tuple(min(1.0, channel * 1.05) for channel in header_bg[:3]) + (header_bg[3],)
        self._header_button_colors.button_active = tuple(max(0.0, channel * 0.95) for channel in header_bg[:3]) + (header_bg[3],)
        self._header_button_colors.text = accent_color[:3] + (1.0,)

        self._weekday_header_colors.text = tuple(
            0.6 * channel + 0.4 * accent_color[index]
            for index, channel in enumerate(text_color[:3])
        ) + (text_color[3],)

        self._day_button_colors.text = text_color
        self._day_button_colors.button = button_color
        self._day_button_colors.button_hovered = button_hovered
        self._day_button_colors.button_active = button_active

        self._selected_day_colors.button = accent_color
        self._selected_day_colors.button_hovered = tuple(min(1.0, channel * 1.2) for channel in accent_color[:3]) + (min(1.0, accent_color[3] * 1.1),)
        self._selected_day_colors.button_active = tuple(min(1.0, channel * 1.4) for channel in accent_color[:3]) + (min(1.0, accent_color[3] * 1.2),)
        self._selected_day_colors.text = (1.0, 1.0, 1.0, 1.0)

        self._today_day_colors.button = today_color
        self._today_day_colors.button_hovered = tuple(min(1.0, channel * 1.2) for channel in today_color[:3]) + (min(1.0, today_color[3] * 1.1),)
        self._today_day_colors.button_active = tuple(min(1.0, channel * 1.4) for channel in today_color[:3]) + (min(1.0, today_color[3] * 1.2),)
        self._today_day_colors.text = (1.0, 1.0, 1.0, 1.0)

        self._disabled_day_colors.text = text_color[:3] + (0.5,)

        if hasattr(self, "_grid") and self._grid:
            self._update_grid()

    def _get_header_text(self) -> str:
        if self._view_level == 0:
            return f"{self.MONTH_NAMES[self._current_month]} {self._current_year}"
        if self._view_level == 1:
            return str(self._current_year)
        return f"{self._current_year_block}-{self._current_year_block + 19}"

    def _update_grid(self) -> None:
        self._header_btn.label = self._get_header_text()

        for child in self._grid.children[:]:
            child.delete_item()

        if self._view_level == 0:
            self._build_day_grid()
        elif self._view_level == 1:
            self._build_month_grid()
        else:
            self._build_year_grid()

    def _build_day_grid(self) -> None:
        table = dcg.Table(
            self.context,
            parent=self._grid,
            flags=dcg.TableFlag.SIZING_STRETCH_SAME | dcg.TableFlag.NO_HOST_EXTEND_X,
            header=False,
        )

        with table.next_row:
            for day in self.WEEKDAY_ABBREV:
                header_cell = dcg.Text(self.context, value=day)
                header_cell.theme = self._weekday_header_colors

        first_day = datetime(self._current_year, self._current_month + 1, 1)
        days_in_month = (
            datetime(
                self._current_year + (self._current_month == 11),
                ((self._current_month + 1) % 12) + 1,
                1,
            )
            - datetime(self._current_year, self._current_month + 1, 1)
        ).days

        if self._current_month == 0:
            prev_month_days = (
                datetime(self._current_year - 1, 12, 1)
                - datetime(self._current_year - 1, 11, 1)
            ).days
        else:
            prev_month_days = (
                datetime(self._current_year, self._current_month + 1, 1)
                - datetime(self._current_year, self._current_month, 1)
            ).days

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        day = 1
        start_weekday = first_day.weekday()

        for week in range(6):
            with table.next_row:
                for weekday in range(7):
                    if week == 0 and weekday < start_weekday:
                        pad_day = prev_month_days - start_weekday + weekday + 1
                        button = dcg.Button(
                            self.context,
                            label=str(pad_day),
                            enabled=False,
                            width=-1,
                        )
                        button.theme = self._disabled_day_colors
                    elif day > days_in_month:
                        next_day = day - days_in_month
                        button = dcg.Button(
                            self.context,
                            label=str(next_day),
                            enabled=False,
                            width=-1,
                        )
                        button.theme = self._disabled_day_colors
                        day += 1
                    else:
                        date = datetime(self._current_year, self._current_month + 1, day)
                        enabled = self._min_date <= date <= self._max_date
                        button = dcg.Button(
                            self.context,
                            label=str(day),
                            enabled=enabled,
                            callback=self._on_day_select,
                            width=-1,
                        )

                        is_selected = date.date() == self.value_as_datetime.date()
                        is_today = date.date() == today.date()
                        if is_selected:
                            button.theme = self._selected_day_colors
                        elif is_today:
                            button.theme = self._today_day_colors
                        else:
                            button.theme = self._day_button_colors

                        day += 1

            if day > days_in_month and week >= 3:
                break

    def _build_month_grid(self) -> None:
        table = dcg.Table(
            self.context,
            parent=self._grid,
            flags=dcg.TableFlag.SIZING_STRETCH_SAME | dcg.TableFlag.NO_HOST_EXTEND_X,
            header=False,
        )
        selected_date = self.value_as_datetime
        month = 0
        for _row in range(3):
            with table.next_row:
                for _col in range(4):
                    enabled = (
                        self._min_date.year < self._current_year
                        or (
                            self._min_date.year == self._current_year
                            and self._min_date.month <= month + 1
                        )
                    )
                    enabled &= (
                        self._max_date.year > self._current_year
                        or (
                            self._max_date.year == self._current_year
                            and self._max_date.month >= month + 1
                        )
                    )

                    button = dcg.Button(
                        self.context,
                        label=self.MONTH_ABBREV[month],
                        enabled=enabled,
                        callback=self._on_month_select,
                        width=-1,
                    )
                    is_selected = (
                        month == selected_date.month - 1
                        and self._current_year == selected_date.year
                    )
                    button.theme = self._selected_day_colors if is_selected else self._day_button_colors
                    month += 1

    def _build_year_grid(self) -> None:
        table = dcg.Table(
            self.context,
            parent=self._grid,
            flags=dcg.TableFlag.SIZING_STRETCH_SAME | dcg.TableFlag.NO_HOST_EXTEND_X,
            header=False,
        )
        selected_date = self.value_as_datetime
        year = self._current_year_block
        for _row in range(5):
            with table.next_row:
                for _col in range(4):
                    if year <= 2999:
                        enabled = self._min_date.year <= year <= self._max_date.year
                        button = dcg.Button(
                            self.context,
                            label=str(year),
                            enabled=enabled,
                            callback=self._on_year_select,
                            width=-1,
                        )
                        is_selected = year == selected_date.year
                        button.theme = self._selected_day_colors if is_selected else self._day_button_colors
                    year += 1

    def _on_prev_click(self) -> None:
        if self._view_level == 0:
            if self._current_month == 0:
                self._current_month = 11
                self._current_year -= 1
            else:
                self._current_month -= 1
        elif self._view_level == 1:
            self._current_year -= 1
        else:
            self._current_year_block -= 20
        self._update_grid()

    def _on_next_click(self) -> None:
        if self._view_level == 0:
            if self._current_month == 11:
                self._current_month = 0
                self._current_year += 1
            else:
                self._current_month += 1
        elif self._view_level == 1:
            self._current_year += 1
        else:
            self._current_year_block += 20
        self._update_grid()

    def _on_header_click(self) -> None:
        self._view_level = (self._view_level + 1) % 3
        self._update_grid()

    def _on_day_select(self, sender) -> None:
        day = int(sender.label)
        new_date = datetime(self._current_year, self._current_month + 1, day)
        self._set_value_and_run_callbacks(new_date)

    def _on_month_select(self, sender) -> None:
        month = self.MONTH_ABBREV.index(sender.label)
        self._current_month = month
        self._view_level = 0
        self._update_grid()

    def _on_year_select(self, sender) -> None:
        self._current_year = int(sender.label)
        self._view_level = 1
        self._update_grid()

    def _set_value_and_run_callbacks(self, value) -> None:
        self._set_value(value)
        self.run_callbacks()

    def _set_value(self, value) -> None:
        if not isinstance(value, datetime):
            raise ValueError("Value must be a datetime object")
        if not (self._min_date <= value <= self._max_date):
            raise ValueError("Date must be between min_date and max_date")

        self._value.value = value.timestamp()
        self._current_month = value.month - 1
        self._current_year = value.year
        self._current_year_block = value.year - (value.year % 20)
        self._update_grid()

    @property
    def min_date(self) -> datetime:
        return self._min_date

    @min_date.setter
    def min_date(self, value) -> None:
        if not isinstance(value, datetime):
            raise ValueError("min_date must be a datetime object")
        self._min_date = value
        current_date = self.value_as_datetime
        if current_date < self._min_date:
            self._value.value = self._min_date.timestamp()
        self._update_grid()

    @property
    def max_date(self) -> datetime:
        return self._max_date

    @max_date.setter
    def max_date(self, value) -> None:
        if not isinstance(value, datetime):
            raise ValueError("max_date must be a datetime object")
        self._max_date = value
        current_date = self.value_as_datetime
        if current_date > self._max_date:
            self._value.value = self._max_date.timestamp()
        self._update_grid()

    @property
    def value(self) -> float:
        return self._value.value

    @property
    def value_as_datetime(self) -> datetime:
        return datetime.fromtimestamp(self._value.value)

    def run_callbacks(self) -> None:
        for callback in self.callbacks:
            callback(self, self, self.value_as_datetime)


class DateTimePicker(dcg.Layout):
    """A local copy of DearCyGui's DateTimePicker for demo-specific customization."""

    def __init__(self, context, *, value=None, min_date=None, max_date=None,
                 layout="horizontal", use_24hr=False, show_seconds=True, **kwargs) -> None:
        super().__init__(context, **kwargs)

        initial_value = value if isinstance(value, datetime) else datetime.now()
        self._is_initializing = True

        if layout == "compact":
            with dcg.HorizontalLayout(context, parent=self):
                self._date_picker = DatePicker(
                    context,
                    value=initial_value,
                    min_date=min_date,
                    max_date=max_date,
                    callbacks=[self._on_change],
                    width=250,
                )
                dcg.Text(context, value=" @ ", width=20)
                self._time_picker = TimePicker(
                    context,
                    value=initial_value,
                    use_24hr=use_24hr,
                    show_seconds=show_seconds,
                    callbacks=[self._on_change],
                    width=250,
                )
        else:
            container = (dcg.HorizontalLayout if layout == "horizontal" else dcg.VerticalLayout)(
                context,
                parent=self,
            )
            with container:
                self._date_picker = DatePicker(
                    context,
                    value=initial_value,
                    min_date=min_date,
                    max_date=max_date,
                    callbacks=[self._on_change],
                )
                self._time_picker = TimePicker(
                    context,
                    value=initial_value,
                    use_24hr=use_24hr,
                    show_seconds=show_seconds,
                    callbacks=[self._on_change],
                )

        if value is not None:
            self.value = value
        else:
            self.value = datetime.now()
        self._is_initializing = False

    def _on_change(self, sender, target, value) -> None:
        if self._is_initializing:
            return
        self.run_callbacks()

    @property
    def value(self):
        return self.value_as_datetime.timestamp()

    @value.setter
    def value(self, value) -> None:
        dt_value = value if isinstance(value, datetime) else datetime.fromtimestamp(float(value))
        self._date_picker._set_value(dt_value)
        self._time_picker.value = dt_value

    @property
    def value_as_datetime(self) -> datetime:
        date_value = self._date_picker.value_as_datetime
        time_value = self._time_picker.value_as_datetime
        return datetime(
            date_value.year,
            date_value.month,
            date_value.day,
            time_value.hour,
            time_value.minute,
            time_value.second,
        )

    @value_as_datetime.setter
    def value_as_datetime(self, value) -> None:
        if not isinstance(value, datetime):
            raise ValueError("Value must be a datetime object")
        self.value = value

    def run_callbacks(self):
        for callback in self.callbacks:
            callback(self, self, self.value_as_datetime)

    @property
    def use_24hr(self) -> bool:
        return self._time_picker.use_24hr

    @use_24hr.setter
    def use_24hr(self, value) -> None:
        self._time_picker.use_24hr = value

    @property
    def show_seconds(self) -> bool:
        return self._time_picker.show_seconds

    @show_seconds.setter
    def show_seconds(self, value) -> None:
        self._time_picker.show_seconds = value

    @property
    def date_picker(self) -> DatePicker:
        return self._date_picker

    @property
    def time_picker(self) -> TimePicker:
        return self._time_picker