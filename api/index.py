from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import numpy as np
from pathlib import Path

app = FastAPI()

# Enable CORS for POST requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load telemetry data safely
DATA_PATH = Path(__file__).parent.parent / "q-vercel-latency.json"

with open(DATA_PATH) as f:
    telemetry = json.load(f)

class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: float

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/")
def analyze_latency(data: RequestBody):
    response = {}

    for region in data.regions:
        region_records = [
            r for r in telemetry if r["region"] == region
        ]

        latencies = [r["latency_ms"] for r in region_records]
        uptimes = [r["uptime_pct"] for r in region_records]

        response[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 2),
            "breaches": sum(l > data.threshold_ms for l in latencies),
        }

    return response
