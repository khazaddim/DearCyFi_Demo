import math

import numpy as np


class SyntheticCandleStream:
    """Deterministic candle revisions and appends for the DearCyFi demo."""

    def __init__(self, interval: float, seed: int) -> None:
        interval = float(interval)
        if not math.isfinite(interval) or interval <= 0:
            raise ValueError("interval must be finite and positive")
        self.interval = interval
        self._random = np.random.default_rng(int(seed))
        self._revision_count = 0
        self.gap_next = False

    def next_event(
        self,
        *,
        timestamp: float,
        high: float,
        low: float,
        close: float,
        volume: float,
    ) -> tuple[str, float, dict[str, float]]:
        if self._revision_count < 3:
            revised_close = float(close) + float(self._random.normal(0.0, 0.02))
            values = {
                "high": max(float(high), revised_close),
                "low": min(float(low), revised_close),
                "close": revised_close,
                "volume": float(volume) + float(self._random.uniform(1.0, 20.0)),
            }
            self._revision_count += 1
            return "update", float(timestamp), values

        next_timestamp = float(timestamp) + self.interval * (2.5 if self.gap_next else 1.0)
        next_close = float(close) + float(self._random.normal(0.0, 0.05))
        next_open = float(close)
        values = {
            "open": next_open,
            "high": max(next_open, next_close) + 0.1,
            "low": min(next_open, next_close) - 0.1,
            "close": next_close,
            "volume": float(self._random.uniform(50.0, 500.0)),
        }
        self.gap_next = False
        self._revision_count = 0
        return "append", next_timestamp, values
