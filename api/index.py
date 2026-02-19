import json
import os
import numpy as np
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# Standard CORS Middleware - usually sufficient on Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry data
telemetry = []
try:
    # Try all possible paths
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "telemetry.json"),
        os.path.join(os.getcwd(), "api", "telemetry.json"),
        os.path.join(os.getcwd(), "telemetry.json"),
        "telemetry.json"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                telemetry = json.load(f)
                break
except Exception as e:
    print(f"Error loading telemetry: {e}")

def get_p95(values):
    if not values: return 0.0
    return float(np.percentile(values, 95))

@app.get("/")
@app.get("/api")
async def root():
    return {"status": "ok", "records": len(telemetry)}

@app.post("/")
@app.post("/api")
async def analytics(request: Request):
    try:
        body = await request.json()
    except:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
        
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    results = {}
    for region in regions:
        region_data = [r for r in telemetry if r.get("region") == region]
        if not region_data:
            results[region] = {
                "avg_latency": 0.0,
                "p95_latency": 0.0,
                "avg_uptime": 0.0,
                "breaches": 0
            }
            continue

        latencies = [float(r.get("latency_ms", 0)) for r in region_data]
        uptimes = [float(r.get("uptime_pct", 0)) for r in region_data]

        results[region] = {
            "avg_latency": round(float(np.mean(latencies)), 4),
            "p95_latency": round(float(get_p95(latencies)), 4),
            "avg_uptime": round(float(np.mean(uptimes)), 4),
            "breaches": int(sum(1 for l in latencies if l > threshold_ms))
        }

    return results