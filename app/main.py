import asyncio
import random
import time

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from prometheus_client import (
    CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest,
)
from fastapi.responses import Response

app = FastAPI(title="orders-service")

REQUESTS = Counter("http_requests_total", "Total HTTP requests", ["method", "path", "status"])
LATENCY = Histogram(
    "http_request_duration_seconds", "Request latency in seconds", ["path"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)
INFLIGHT = Gauge("http_requests_in_flight", "Requests currently being served")

# Fault-injection state, used to rehearse incidents
CHAOS = {"error_rate": 0.0, "latency_ms": 0}


class Chaos(BaseModel):
    error_rate: float = Field(0.0, ge=0, le=1)
    latency_ms: int = Field(0, ge=0, le=5000)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    path = request.url.path
    if path == "/metrics":
        return await call_next(request)
    INFLIGHT.inc()
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        LATENCY.labels(path).observe(time.perf_counter() - start)
        REQUESTS.labels(request.method, path, str(status)).inc()
        INFLIGHT.dec()


@app.get("/healthz")
def healthz():
    return {"status": "alive"}


@app.get("/readyz")
def readyz():
    return {"status": "ready"}


@app.get("/orders")
async def orders():
    await asyncio.sleep(random.uniform(0.01, 0.05) + CHAOS["latency_ms"] / 1000)
    if random.random() < CHAOS["error_rate"]:
        raise HTTPException(status_code=500, detail="injected failure")
    return {"orders": [{"id": i, "total": round(random.uniform(10, 200), 2)} for i in range(3)]}


@app.post("/chaos")
def set_chaos(cfg: Chaos):
    CHAOS.update(cfg.model_dump())
    return CHAOS


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
