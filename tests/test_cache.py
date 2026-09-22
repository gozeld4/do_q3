import pytest

from app.cache import FlagCache, FlagSnapshot


def test_snapshot_copies_and_protects_overrides() -> None:
    source = {"user-123": True}
    snapshot = FlagSnapshot(global_enabled=False, overrides=source)
    source["user-123"] = False

    assert snapshot.overrides["user-123"] is True
    with pytest.raises(TypeError):
        snapshot.overrides["user-123"] = False  # type: ignore[index]


def test_cache_enforces_entry_limit_and_supports_invalidation() -> None:
    cache = FlagCache(max_entries=1, ttl_seconds=60)
    first = FlagSnapshot(global_enabled=False, overrides={})
    second = FlagSnapshot(global_enabled=True, overrides={})

    cache.set("first", first)
    cache.set("second", second)

    assert cache.get("first") is None
    assert cache.get("second") == second

    cache.invalidate("second")
    assert cache.get("second") is None
