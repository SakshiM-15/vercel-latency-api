from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import numpy as np
from pathlib import Path
from fastapi.responses import JSONResponse

app = FastAPI()

# ✅ FULL CORS CONFIG (important)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # allow all origins
    allow_credentials=False,      # MUST be False when using "*"
    allow_methods=["*"],          # allow POST, OPTIONS, etc.
    allow_headers=["*"],          # allow all headers
)

# Load telemetry data
DATA_PATH = Path(__file__).parent.parent / "q-vercel-latency.json"
with open(DATA_PATH) as f:
    telemetry = json.load(f)

class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: float

@app.get("/")
def health():
    return {"status": "ok"}

# ✅ Explicit OPTIONS handler (critical for Vercel)
@app.options("/")
def options_handler():
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
        region_records = [r for r in telemetry if r["region"] == region]

        latencies = [r["latency_ms"] for r in region_records]
        uptimes = [r["uptime_pct"] for r in region_records]

        response[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 2),
            "breaches": sum(l > data.threshold_ms for l in latencies),
        }

    return response
