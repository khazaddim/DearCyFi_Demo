from datetime import datetime, timezone

import dearcygui as dcg
import numpy as np

from .base import DataLoadResult, DataRequest, PlotSeries


PROVIDER_ID = "toy-econometric"


def load_toy_econometric_data(request: DataRequest) -> DataLoadResult:
    if request.provider_id != PROVIDER_ID:
        raise ValueError(f"Unsupported provider ID: {request.provider_id!r}")
    if request.interval not in {None, "weekly"}:
        raise ValueError("Toy econometric data supports only the weekly interval")

    periods = int(request.filters.get("periods", 52))
    seed = int(request.filters.get("seed", 2026))
    if periods <= 0:
        raise ValueError("periods must be positive")
    start = request.start or datetime(2024, 1, 5, tzinfo=timezone.utc)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)

    first_timestamp = start.timestamp()
    timestamps = first_timestamp + np.arange(periods, dtype=float) * 7 * 86400
    random = np.random.default_rng(seed)
    trend = np.linspace(100.0, 112.0, periods)
    cycle = 4.0 * np.sin(np.arange(periods, dtype=float) * np.pi / 8.0)
    values = trend + cycle + random.normal(0.0, 0.6, periods)

    return DataLoadResult(
        provider_id=PROVIDER_ID,
        dataset_id=request.dataset_id,
        display_name="Toy Weekly Liquidity Index",
        series=[
            PlotSeries(
                name="Toy Weekly Liquidity",
                kind="line",
                timestamps=timestamps,
                values={"value": values},
                metadata={
                    "frequency": "weekly",
                    "seed": seed,
                    "timezone": "UTC",
                    "source": "deterministic toy generator",
                },
            )
        ],
        metadata={"generated": True},
    )


class ToyEconometricDataWidget(dcg.ChildWindow):
    provider_id = PROVIDER_ID
    display_name = "Toy Econometric Data"

    def __init__(self, context, *, on_load_requested=None, on_status=None, **kwargs):
        super().__init__(context, **kwargs)
        self.on_load_requested = on_load_requested
        self.on_status = on_status

        with self:
            dcg.Text(context, value="Weekly liquidity index")
            self.periods = dcg.Slider(
                context,
                label="Observations",
                min_value=8,
                max_value=156,
                value=52,
                print_format="%.0f",
                width="fillx",
            )
            self.seed = dcg.InputValue(context, label="Seed", value=2026, width="fillx")
            dcg.Button(
                context,
                label="Load Weekly Series",
                width="fillx",
                callback=self._request_load,
            )

    def build_request(self) -> DataRequest:
        return DataRequest(
            provider_id=self.provider_id,
            dataset_id="weekly-liquidity",
            interval="weekly",
            filters={"periods": int(self.periods.value), "seed": int(self.seed.value)},
        )

    def load(self, request: DataRequest) -> DataLoadResult:
        return load_toy_econometric_data(request)

    def dispose(self) -> None:
        return None

    def _request_load(self, sender=None, app_data=None, user_data=None) -> None:
        request = self.build_request()
        if callable(self.on_load_requested):
            self.on_load_requested(self, request)
        elif callable(self.on_status):
            self.on_status("No host callback is configured for the toy provider.")