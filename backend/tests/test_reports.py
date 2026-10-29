"""Automated Test Suite for Report Summary API.

Tests aggregated database calculations, module distribution, execution status
breakdown, and timestamp tracking across empty and populated database states.
"""

from fastapi.testclient import TestClient

from app.core.config import settings


def test_report_summary_empty_database(client: TestClient) -> None:
    """Requirement: GET /api/reports/summary returns zero counts and null timestamp on empty DB."""
    response = client.get(f"{settings.API_PREFIX}/reports/summary")
    assert response.status_code == 200

    data = response.json()
    assert data["total_experiments"] == 0
    assert data["by_module"]["protection"] == 0
    assert data["by_module"]["decentralization"] == 0
    assert data["by_module"]["efficiency"] == 0
    assert data["by_status"]["pending"] == 0
    assert data["by_status"]["completed"] == 0
    assert data["by_status"]["failed"] == 0
    assert data["latest_experiment_at"] is None


def test_report_summary_populated_database(client: TestClient) -> None:
    """Requirement: Accurately computes totals and breakdowns across multiple experiments."""
    # Seed 2 protection, 1 decentralization, 1 efficiency
    client.post(
        f"{settings.API_PREFIX}/experiments",
        json={"module": "protection", "scenario": "prot_1", "input_parameters": {"a": 1}},
    )
    client.post(
        f"{settings.API_PREFIX}/experiments",
        json={"module": "protection", "scenario": "prot_2", "input_parameters": {"a": 2}},
    )
    client.post(
        f"{settings.API_PREFIX}/experiments",
        json={"module": "decentralization", "scenario": "dec_1", "input_parameters": {"b": 1}},
    )
    client.post(
        f"{settings.API_PREFIX}/experiments",
        json={"module": "efficiency", "scenario": "eff_1", "input_parameters": {"c": 1}},
    )

    response = client.get(f"{settings.API_PREFIX}/reports/summary")
    assert response.status_code == 200

    data = response.json()
    assert data["total_experiments"] == 4
    assert data["by_module"]["protection"] == 2
    assert data["by_module"]["decentralization"] == 1
    assert data["by_module"]["efficiency"] == 1
    assert data["by_status"]["pending"] == 4
    assert data["latest_experiment_at"] is not None
