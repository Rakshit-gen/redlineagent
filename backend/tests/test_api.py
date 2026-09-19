import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.db import get_session
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _seed_rule(client):
    return client.post(
        "/api/policy-rules/",
        json={
            "topic": "auto_renewal",
            "guidance": "Auto-renewal without an opt-out window locks you in.",
            "severity": "high",
            "risk_keywords": "automatically renew,auto-renew",
            "fallback_language": "Renews only on mutual written consent.",
        },
    ).json()


def test_create_and_list_contracts(client):
    client.post("/api/contracts/", json={"vendor_name": "Acme", "raw_text": "Fixed term contract."})
    resp = client.get("/api/contracts/")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_analyze_contract_creates_a_run_with_flags(client):
    _seed_rule(client)
    contract = client.post(
        "/api/contracts/",
        json={"vendor_name": "Acme", "raw_text": "This Agreement will automatically renew each year."},
    ).json()

    resp = client.post(f"/api/contracts/{contract['id']}/analyze/")
    assert resp.status_code == 200
    run = resp.json()
    assert run["status"] == "completed"
    assert len(run["flags"]) == 1


def test_cannot_reanalyze_a_reviewed_contract(client):
    _seed_rule(client)
    contract = client.post(
        "/api/contracts/", json={"vendor_name": "Acme", "raw_text": "Fixed term contract."}
    ).json()
    client.post(f"/api/contracts/{contract['id']}/analyze/")

    resp = client.post(f"/api/contracts/{contract['id']}/analyze/")
    assert resp.status_code == 409


def test_dismiss_flag(client):
    _seed_rule(client)
    contract = client.post(
        "/api/contracts/",
        json={"vendor_name": "Acme", "raw_text": "This Agreement will automatically renew each year."},
    ).json()
    run = client.post(f"/api/contracts/{contract['id']}/analyze/").json()
    flag_id = run["flags"][0]["id"]

    resp = client.post(f"/api/flags/{flag_id}/dismiss/", json={"dismissed": True})
    assert resp.status_code == 200
    assert resp.json()["dismissed"] is True


def test_export_csv(client):
    resp = client.get("/api/runs/export/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")


def test_contract_not_found(client):
    resp = client.get("/api/contracts/999/")
    assert resp.status_code == 404


def test_analyzing_a_nonexistent_contract_404s(client):
    resp = client.post("/api/contracts/999/analyze/")
    assert resp.status_code == 404


def test_contract_report_csv_includes_flags(client):
    _seed_rule(client)
    contract = client.post(
        "/api/contracts/",
        json={"vendor_name": "Acme Co", "raw_text": "This Agreement will automatically renew each year."},
    ).json()
    client.post(f"/api/contracts/{contract['id']}/analyze/")

    resp = client.get(f"/api/contracts/{contract['id']}/report/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "auto_renewal" in resp.text


def test_contract_report_csv_for_unanalyzed_contract_is_header_only(client):
    contract = client.post(
        "/api/contracts/", json={"vendor_name": "Acme Co", "raw_text": "Fixed term contract."}
    ).json()

    resp = client.get(f"/api/contracts/{contract['id']}/report/")
    assert resp.status_code == 200
    assert resp.text.strip().count("\n") == 0
