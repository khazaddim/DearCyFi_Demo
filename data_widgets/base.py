from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Mapping, Sequence


@dataclass(frozen=True)
class DataRequest:
    provider_id: str
    dataset_id: str
    start: datetime | None = None
    end: datetime | None = None
    interval: str | None = None
    filters: Mapping[str, object] = field(default_factory=dict)


@dataclass
class PlotSeries:
    name: str
    kind: Literal["candles", "line", "bars"]
    timestamps: Sequence
    values: Mapping[str, Sequence]
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass
class DataLoadResult:
    provider_id: str
    dataset_id: str
    display_name: str
    series: Sequence[PlotSeries]
    metadata: Mapping[str, object] = field(default_factory=dict)