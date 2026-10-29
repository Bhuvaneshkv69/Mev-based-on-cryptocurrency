"""Automated Test Suite for Experiment Management API.

Tests experiment registration, validation constraints, retrieval, pagination,
filtering, metadata updates, deletion, and safety checks.
"""

from fastapi.testclient import TestClient

from app.core.config import settings


def test_create_experiment_success(client: TestClient) -> None:
    """Requirement: POST /api/experiments creates a pending experiment record."""
    payload = {
        "module": "protection",
        "scenario": "frontrunning_sandwich_dex",
        "input_parameters": {
            "token_in": "WETH",
            "token_out": "USDC",
            "amount_in": 10.0,
            "slippage_bps": 50,
        },
        "assumptions": {
            "mempool_latency_ms": 120,
            "data_source": "synthetic",
        },
    }

    response = client.post(f"{settings.API_PREFIX}/experiments", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["id"] > 0
    assert data["module"] == "protection"
    assert data["scenario"] == "frontrunning_sandwich_dex"
    assert data["status"] == "pending"
    assert data["results"] is None  # Must remain null until simulation execution in Phase 3
    assert data["input_parameters"]["amount_in"] == 10.0
    assert data["assumptions"]["data_source"] == "synthetic"
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


def test_create_experiment_invalid_module(client: TestClient) -> None:
    """Requirement: Enforce that only documented modules can be registered."""
    payload = {
        "module": "unsupported_crypto_module",
        "scenario": "test_scenario",
        "input_parameters": {"param": 1},
    }

    response = client.post(f"{settings.API_PREFIX}/experiments", json=payload)
    assert response.status_code == 422
    assert "Invalid module" in response.text


def test_create_experiment_empty_inputs(client: TestClient) -> None:
    """Requirement: input_parameters cannot be empty or invalid."""
    payload = {
        "module": "efficiency",
        "scenario": "gas_auction_competition",
        "input_parameters": {},
    }

    response = client.post(f"{settings.API_PREFIX}/experiments", json=payload)
    assert response.status_code == 422


def test_create_experiment_ignores_client_tampered_status_and_results(client: TestClient) -> None:
    """Requirement: Clients cannot force 'completed' status or inject fake results on create."""
    payload = {
        "module": "decentralization",
        "scenario": "relay_market_share",
        "input_parameters": {"builder_count": 5},
        # Tampered client fields that should NOT be allowed or accepted
        "status": "completed",
        "results": {"fabricated_savings": 999999},
        "id": 9999,
    }

    response = client.post(f"{settings.API_PREFIX}/experiments", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["id"] != 9999  # ID must be database-assigned
    assert data["status"] == "pending"  # Must remain pending
    assert data["results"] is None  # Must ignore fabricated results


def test_get_experiment_by_id_success(client: TestClient) -> None:
    """Requirement: GET /api/experiments/{id} retrieves the created record."""
    create_res = client.post(
        f"{settings.API_PREFIX}/experiments",
        json={
            "module": "decentralization",
            "scenario": "pbs_relay_sim",
            "input_parameters": {"relays": ["relay-a", "relay-b"]},
        },
    )
    created_id = create_res.json()["id"]

    response = client.get(f"{settings.API_PREFIX}/experiments/{created_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == created_id
    assert data["module"] == "decentralization"
    assert data["scenario"] == "pbs_relay_sim"


def test_get_experiment_not_found(client: TestClient) -> None:
    """Requirement: GET /api/experiments/{id} returns 404 for nonexistent record."""
    response = client.get(f"{settings.API_PREFIX}/experiments/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_experiments_pagination(client: TestClient) -> None:
    """Requirement: GET /api/experiments supports pagination metadata."""
    # Create 3 experiments
    for i in range(3):
        client.post(
            f"{settings.API_PREFIX}/experiments",
            json={
                "module": "efficiency",
                "scenario": f"gas_scenario_{i}",
                "input_parameters": {"base_fee": 20 + i},
            },
        )

    # Request page 1 with page_size 2
    res = client.get(f"{settings.API_PREFIX}/experiments?page=1&page_size=2")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 2

    # Request page 2 with page_size 2
    res_p2 = client.get(f"{settings.API_PREFIX}/experiments?page=2&page_size=2")
    assert res_p2.status_code == 200
    data_p2 = res_p2.json()
    assert len(data_p2["items"]) == 1


def test_list_experiments_filtering(client: TestClient) -> None:
    """Requirement: GET /api/experiments allows filtering by module and status."""
    client.post(
        f"{settings.API_PREFIX}/experiments",
        json={"module": "protection", "scenario": "sc_1", "input_parameters": {"a": 1}},
    )
    client.post(
        f"{settings.API_PREFIX}/experiments",
        json={"module": "efficiency", "scenario": "sc_2", "input_parameters": {"b": 2}},
    )

    # Filter by module = protection
    res_mod = client.get(f"{settings.API_PREFIX}/experiments?module=protection")
    assert res_mod.status_code == 200
    data_mod = res_mod.json()
    assert data_mod["total"] == 1
    assert data_mod["items"][0]["module"] == "protection"

    # Filter by status = pending
    res_status = client.get(f"{settings.API_PREFIX}/experiments?status=pending")
    assert res_status.status_code == 200
    assert res_status.json()["total"] == 2


def test_update_experiment_metadata(client: TestClient) -> None:
    """Requirement: PATCH /api/experiments/{id} updates safe metadata only."""
    create_res = client.post(
        f"{settings.API_PREFIX}/experiments",
        json={
            "module": "protection",
            "scenario": "initial_scenario_label",
            "input_parameters": {"trade_amount": 50},
            "assumptions": {"note": "initial assumption"},
        },
    )
    exp_id = create_res.json()["id"]

    patch_payload = {
        "scenario": "revised_scenario_label",
        "assumptions": {"note": "updated assumption"},
    }
    patch_res = client.patch(f"{settings.API_PREFIX}/experiments/{exp_id}", json=patch_payload)
    assert patch_res.status_code == 200

    data = patch_res.json()
    assert data["scenario"] == "revised_scenario_label"
    assert data["assumptions"]["note"] == "updated assumption"
    assert data["status"] == "pending"  # Status remains pending


def test_update_experiment_not_found(client: TestClient) -> None:
    """Requirement: PATCH returns 404 if record doesn't exist."""
    res = client.patch(
        f"{settings.API_PREFIX}/experiments/999999",
        json={"scenario": "new_name"},
    )
    assert res.status_code == 404


def test_delete_experiment_success(client: TestClient) -> None:
    """Requirement: DELETE /api/experiments/{id} deletes the record."""
    create_res = client.post(
        f"{settings.API_PREFIX}/experiments",
        json={
            "module": "efficiency",
            "scenario": "to_be_deleted",
            "input_parameters": {"gas_limit": 30000000},
        },
    )
    exp_id = create_res.json()["id"]

    del_res = client.delete(f"{settings.API_PREFIX}/experiments/{exp_id}")
    assert del_res.status_code == 204

    # Verify subsequent GET returns 404
    get_res = client.get(f"{settings.API_PREFIX}/experiments/{exp_id}")
    assert get_res.status_code == 404


def test_delete_experiment_not_found(client: TestClient) -> None:
    """Requirement: DELETE returns 404 if record does not exist."""
    del_res = client.delete(f"{settings.API_PREFIX}/experiments/999999")
    assert del_res.status_code == 404
