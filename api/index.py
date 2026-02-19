import json
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Strategy 1: Standard CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Strategy 2: Aggressive Middleware for all requests
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = JSONResponse({"status": "ok"})
    else:
        response = await call_next(request)
    
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Load telemetry data
_data_path = os.path.join(os.path.dirname(__file__), "telemetry.json")
try:
    with open(_data_path, "r") as f:
        telemetry = json.load(f)
except Exception:
    telemetry = []

def get_p95(values):
    if not values: return 0.0
    sorted_values = sorted(values)
    idx = int(0.95 * len(sorted_values))
    return sorted_values[min(idx, len(sorted_values)-1)]

@app.get("/")
@app.get("/api")
async def root():
    return JSONResponse({"status": "ready", "cors": "enabled"})

@app.post("/api")
@app.post("/")
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
            "avg_latency": round(sum(latencies) / len(latencies), 4),
            "p95_latency": round(float(get_p95(latencies)), 4),
            "avg_uptime": round(sum(uptimes) / len(uptimes), 4),
            "breaches": sum(1 for l in latencies if l > threshold_ms)
        }

    return JSONResponse(results)