from collections.abc import Callable


class DataWidgetRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, Callable] = {}

    def register(self, provider_id: str, factory: Callable) -> None:
        if not provider_id or provider_id in self._factories:
            raise ValueError(f"Provider ID is already registered or invalid: {provider_id!r}")
        self._factories[provider_id] = factory

    def get(self, provider_id: str) -> Callable:
        try:
            return self._factories[provider_id]
        except KeyError as exc:
            raise ValueError(f"Unknown data provider ID: {provider_id!r}") from exc

    @property
    def provider_ids(self) -> tuple[str, ...]:
        return tuple(self._factories)