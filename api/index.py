import json
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# Note: CORS is now handled globally in vercel.json to ensure consistency

# Load telemetry data
_data_path = os.path.join(os.path.dirname(__file__), "telemetry.json")
try:
    with open(_data_path, "r") as f:
        telemetry = json.load(f)
except Exception as e:
    try:
        # Fallback for different build structures
        with open("api/telemetry.json", "r") as f:
             telemetry = json.load(f)
    except:
        telemetry = []

def get_p95(values):
    if not values: return 0.0
    sorted_values = sorted(values)
    idx = int(0.95 * len(sorted_values))
    return sorted_values[min(idx, len(sorted_values)-1)]

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/api")
@app.post("/")
async def analytics(request: Request):
    # Handle preflight manually if needed, though vercel.json should cover it
    if request.method == "OPTIONS":
        return JSONResponse({"status": "ok"})

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
            "avg_latency": round(sum(latencies) / len(latencies), 4),
            "p95_latency": round(float(get_p95(latencies)), 4),
            "avg_uptime": round(sum(uptimes) / len(uptimes), 4),
            "breaches": sum(1 for l in latencies if l > threshold_ms)
        }

    return JSONResponse(results)