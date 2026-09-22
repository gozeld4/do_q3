import pytest
from fastapi.testclient import TestClient
from httpx import Response


def assert_error(response: Response, status_code: int, code: str) -> None:
    assert response.status_code == status_code
    body = response.json()
    assert body["error"]["code"] == code
    assert isinstance(body["error"]["message"], str)


def create_flag(client: TestClient, key: str = "checkout_v2") -> dict[str, object]:
    response = client.post(
        "/flags",
        json={
            "key": key,
            "description": "New checkout",
            "enabled": False,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_flag_crud(client: TestClient) -> None:
    create_response = client.post(
        "/flags",
        json={
            "key": "checkout_v2",
            "description": "New checkout",
            "enabled": False,
        },
    )
    assert create_response.status_code == 201
    assert create_response.headers["location"] == "/flags/checkout_v2"
    assert create_response.json()["key"] == "checkout_v2"

    list_response = client.get("/flags", params={"limit": 10, "offset": 0})
    assert list_response.status_code == 200
    assert [flag["key"] for flag in list_response.json()] == ["checkout_v2"]

    get_response = client.get("/flags/checkout_v2")
    assert get_response.status_code == 200
    assert get_response.json()["description"] == "New checkout"

    patch_response = client.patch(
        "/flags/checkout_v2",
        json={"description": "Updated checkout", "enabled": True},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["description"] == "Updated checkout"
    assert patch_response.json()["enabled"] is True

    delete_response = client.delete("/flags/checkout_v2")
    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert_error(client.get("/flags/checkout_v2"), 404, "flag_not_found")


def test_duplicate_flag_returns_conflict(client: TestClient) -> None:
    create_flag(client)

    response = client.post("/flags", json={"key": "checkout_v2"})

    assert_error(response, 409, "duplicate_flag")


@pytest.mark.parametrize(
    "payload",
    [
        {"key": "x"},
        {"key": "Uppercase"},
        {"key": "valid_key", "unexpected": True},
        {"key": "valid_key", "description": "x" * 501},
    ],
)
def test_create_flag_rejects_invalid_bodies(
    client: TestClient,
    payload: dict[str, object],
) -> None:
    assert_error(client.post("/flags", json=payload), 422, "validation_error")


@pytest.mark.parametrize("payload", [{}, {"description": None}, {"enabled": None}])
def test_patch_rejects_empty_or_null_changes(
    client: TestClient,
    payload: dict[str, object],
) -> None:
    create_flag(client)

    response = client.patch("/flags/checkout_v2", json=payload)

    assert_error(response, 422, "validation_error")


@pytest.mark.parametrize(
    "params",
    [{"limit": 0}, {"limit": 101}, {"offset": -1}],
)
def test_list_rejects_invalid_pagination(
    client: TestClient,
    params: dict[str, int],
) -> None:
    assert_error(
        client.get("/flags", params=params),
        422,
        "validation_error",
    )


def test_override_create_update_and_delete(client: TestClient) -> None:
    create_flag(client)

    create_response = client.put(
        "/flags/checkout_v2/users/%20user-123%20",
        json={"enabled": True},
    )
    assert create_response.status_code == 201
    assert create_response.json()["user_id"] == "user-123"
    override_id = create_response.json()["id"]

    update_response = client.put(
        "/flags/checkout_v2/users/user-123",
        json={"enabled": False},
    )
    assert update_response.status_code == 200
    assert update_response.json()["id"] == override_id
    assert update_response.json()["enabled"] is False

    delete_response = client.delete("/flags/checkout_v2/users/user-123")
    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert_error(
        client.delete("/flags/checkout_v2/users/user-123"),
        404,
        "override_not_found",
    )


def test_override_requires_an_existing_flag(client: TestClient) -> None:
    response = client.put(
        "/flags/missing/users/user-123",
        json={"enabled": True},
    )

    assert_error(response, 404, "flag_not_found")


@pytest.mark.parametrize("user_id", ["%20%20%20", "x" * 256])
def test_override_rejects_invalid_user_ids(
    client: TestClient,
    user_id: str,
) -> None:
    create_flag(client)

    response = client.put(
        f"/flags/checkout_v2/users/{user_id}",
        json={"enabled": True},
    )

    assert_error(response, 422, "validation_error")
