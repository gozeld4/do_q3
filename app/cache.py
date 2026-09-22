from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from threading import RLock
from types import MappingProxyType

from cachetools import TTLCache

from app.config import get_settings


@dataclass(frozen=True)
class FlagSnapshot:
    global_enabled: bool
    overrides: Mapping[str, bool]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "overrides",
            MappingProxyType(dict(self.overrides)),
        )


class FlagCache:
    def __init__(self, *, max_entries: int, ttl_seconds: float) -> None:
        self._entries: TTLCache[str, FlagSnapshot] = TTLCache(
            maxsize=max_entries,
            ttl=ttl_seconds,
        )
        self._lock = RLock()

    def get(self, key: str) -> FlagSnapshot | None:
        with self._lock:
            return self._entries.get(key)

    def set(self, key: str, snapshot: FlagSnapshot) -> None:
        with self._lock:
            self._entries[key] = snapshot

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._entries.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


settings = get_settings()
flag_cache = FlagCache(
    max_entries=settings.cache_max_entries,
    ttl_seconds=settings.cache_ttl_seconds,
)


def get_flag_cache() -> FlagCache:
    return flag_cache
