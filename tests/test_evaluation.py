from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.evaluation import evaluate_flag


def assert_error(response: Response, status_code: int, code: str) -> None:
    assert response.status_code == status_code
    assert response.json()["error"]["code"] == code


def create_flag(client: TestClient, *, enabled: bool = False) -> None:
    response = client.post(
        "/flags",
        json={"key": "checkout_v2", "enabled": enabled},
    )
    assert response.status_code == 201


@pytest.mark.parametrize(
    ("global_enabled", "override_enabled", "expected_enabled", "expected_reason"),
    [
        (False, None, False, "global"),
        (True, None, True, "global"),
        (False, True, True, "user_override"),
        (True, False, False, "user_override"),
    ],
)
def test_evaluation_precedence(
    global_enabled: bool,
    override_enabled: bool | None,
    expected_enabled: bool,
    expected_reason: str,
) -> None:
    result = evaluate_flag(
        global_enabled=global_enabled,
        override_enabled=override_enabled,
    )

    assert result.enabled is expected_enabled
    assert result.reason == expected_reason


def test_evaluate_missing_flag(client: TestClient) -> None:
    response = client.get(
        "/flags/missing/evaluate",
        params={"user_id": "user-123"},
    )

    assert_error(response, 404, "flag_not_found")


@pytest.mark.parametrize(
    "params",
    [{}, {"user_id": "   "}, {"user_id": "x" * 256}],
)
def test_evaluate_rejects_invalid_user_id(
    client: TestClient,
    params: dict[str, str],
) -> None:
    create_flag(client)

    response = client.get("/flags/checkout_v2/evaluate", params=params)

    assert_error(response, 422, "validation_error")


def test_evaluate_uses_global_state_and_cache(client: TestClient) -> None:
    create_flag(client, enabled=True)

    first = client.get(
        "/flags/checkout_v2/evaluate",
        params={"user_id": " user-123 "},
    )
    second = client.get(
        "/flags/checkout_v2/evaluate",
        params={"user_id": "user-123"},
    )

    assert first.status_code == 200
    assert first.headers["x-cache"] == "MISS"
    assert first.json() == {
        "flag": "checkout_v2",
        "user_id": "user-123",
        "enabled": True,
        "reason": "global",
    }
    assert second.headers["x-cache"] == "HIT"
    assert second.json() == first.json()


@pytest.mark.parametrize(
    ("global_enabled", "override_enabled"),
    [(False, True), (True, False)],
)
def test_evaluate_prefers_user_override(
    client: TestClient,
    global_enabled: bool,
    override_enabled: bool,
) -> None:
    create_flag(client, enabled=global_enabled)
    override_response = client.put(
        "/flags/checkout_v2/users/user-123",
        json={"enabled": override_enabled},
    )

    response = client.get(
        "/flags/checkout_v2/evaluate",
        params={"user_id": "user-123"},
    )

    assert override_response.status_code == 201
    assert response.json()["enabled"] is override_enabled
    assert response.json()["reason"] == "user_override"


def test_global_update_invalidates_cached_snapshot(client: TestClient) -> None:
    create_flag(client, enabled=False)
    evaluate_url = "/flags/checkout_v2/evaluate"
    params = {"user_id": "user-123"}
    client.get(evaluate_url, params=params)
    assert client.get(evaluate_url, params=params).headers["x-cache"] == "HIT"

    update = client.patch(
        "/flags/checkout_v2",
        json={"enabled": True},
    )
    refreshed = client.get(evaluate_url, params=params)

    assert update.status_code == 200
    assert refreshed.headers["x-cache"] == "MISS"
    assert refreshed.json()["enabled"] is True
    assert refreshed.json()["reason"] == "global"


def test_description_update_invalidates_cached_snapshot(
    client: TestClient,
) -> None:
    create_flag(client)
    evaluate_url = "/flags/checkout_v2/evaluate"
    params = {"user_id": "user-123"}
    client.get(evaluate_url, params=params)

    update = client.patch(
        "/flags/checkout_v2",
        json={"description": "New description"},
    )
    refreshed = client.get(evaluate_url, params=params)

    assert update.status_code == 200
    assert refreshed.headers["x-cache"] == "MISS"
    assert refreshed.json()["enabled"] is False


def test_override_writes_invalidate_cached_snapshot(client: TestClient) -> None:
    create_flag(client, enabled=False)
    evaluate_url = "/flags/checkout_v2/evaluate"
    params = {"user_id": "user-123"}
    client.get(evaluate_url, params=params)

    created = client.put(
        "/flags/checkout_v2/users/user-123",
        json={"enabled": True},
    )
    after_create = client.get(evaluate_url, params=params)

    updated = client.put(
        "/flags/checkout_v2/users/user-123",
        json={"enabled": False},
    )
    after_update = client.get(evaluate_url, params=params)

    deleted = client.delete("/flags/checkout_v2/users/user-123")
    after_delete = client.get(evaluate_url, params=params)

    assert created.status_code == 201
    assert after_create.headers["x-cache"] == "MISS"
    assert after_create.json()["enabled"] is True
    assert after_create.json()["reason"] == "user_override"
    assert updated.status_code == 200
    assert after_update.headers["x-cache"] == "MISS"
    assert after_update.json()["enabled"] is False
    assert after_update.json()["reason"] == "user_override"
    assert deleted.status_code == 204
    assert after_delete.headers["x-cache"] == "MISS"
    assert after_delete.json()["enabled"] is False
    assert after_delete.json()["reason"] == "global"


def test_delete_flag_invalidates_cached_snapshot(client: TestClient) -> None:
    create_flag(client)
    evaluate_url = "/flags/checkout_v2/evaluate"
    params = {"user_id": "user-123"}
    client.get(evaluate_url, params=params)

    deleted = client.delete("/flags/checkout_v2")
    response = client.get(evaluate_url, params=params)

    assert deleted.status_code == 204
    assert_error(response, 404, "flag_not_found")
