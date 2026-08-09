from .base import DataLoadResult, DataRequest, PlotSeries
from .registry import DataWidgetRegistry
from .toy_econometric import PROVIDER_ID, ToyEconometricDataWidget, load_toy_econometric_data


DATA_WIDGETS = DataWidgetRegistry()
DATA_WIDGETS.register(PROVIDER_ID, ToyEconometricDataWidget)

__all__ = [
    "DATA_WIDGETS",
    "DataLoadResult",
    "DataRequest",
    "DataWidgetRegistry",
    "PlotSeries",
    "ToyEconometricDataWidget",
    "load_toy_econometric_data",
]