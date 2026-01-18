from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
import numpy as np
from pathlib import Path

app = FastAPI()

# CORS middleware (keep this)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=False,
)

# Load telemetry data
DATA_PATH = Path(__file__).parent.parent / "q-vercel-latency.json"
with open(DATA_PATH) as f:
    telemetry = json.load(f)

class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: float

@app.options("/")
def preflight():
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

@app.post("/")
def analyze_latency(data: RequestBody):
    response = {}

    for region in data.regions:
        records = [r for r in telemetry if r["region"] == region]

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        response[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 2),
            "breaches": sum(l > data.threshold_ms for l in latencies),
        }

    # 🔥 FORCE CORS HEADER ON RESPONSE (THIS IS THE KEY)
    return JSONResponse(
        content=response,
        headers={
            "Access-Control-Allow-Origin": "*"
        },
    )
