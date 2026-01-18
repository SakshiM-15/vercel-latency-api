from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import numpy as np

app = FastAPI()

# Enable CORS (required)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load telemetry data
with open("q-vercel-latency.json") as f:
    telemetry = json.load(f)

class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: int

@app.post("/")
def analyze_latency(data: RequestBody):
    result = {}

    for region in data.regions:
        records = [r for r in telemetry if r["region"] == region]

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime"] for r in records]

        result[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": sum(l > data.threshold_ms for l in latencies)
        }

    return result
