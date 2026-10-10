from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    assert client.get("/healthz").status_code == 200


def test_orders_ok():
    client.post("/chaos", json={"error_rate": 0, "latency_ms": 0})
    assert client.get("/orders").status_code == 200


def test_chaos_causes_errors():
    client.post("/chaos", json={"error_rate": 1, "latency_ms": 0})
    assert client.get("/orders").status_code == 500
    client.post("/chaos", json={"error_rate": 0, "latency_ms": 0})


def test_metrics_exposed():
    client.get("/orders")
    body = client.get("/metrics").text
    assert "http_requests_total" in body
