import json
import os
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI()

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Expose-Headers": "Access-Control-Allow-Origin",
}

@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        try:
            response = await call_next(request)
        except Exception as e:
            response = JSONResponse(content={"error": str(e)}, status_code=500)
    
    for key, value in CORS_HEADERS.items():
        response.headers[key] = value
    return response

# Load telemetry data
telemetry = []
_data_path = os.path.join(os.path.dirname(__file__), "telemetry.json")
if os.path.exists(_data_path):
    with open(_data_path, "r") as f:
        telemetry = json.load(f)

def calculate_p95(lats):
    if not lats: return 0.0
    lats = sorted(lats)
    n = len(lats)
    idx = int(0.95 * n)
    return lats[min(idx, n - 1)]

@app.get("/")
@app.get("/api")
@app.get("/health")
async def health():
    return {"status": "ok", "records": len(telemetry)}

@app.post("/")
@app.post("/api")
async def analytics(request: Request):
    try:
        data = await request.json()
    except:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    regions = data.get("regions", [])
    threshold = data.get("threshold_ms", 180)

    results = {}
    for region in regions:
        recs = [r for r in telemetry if str(r.get("region", "")).lower() == str(region).lower()]
        if not recs:
            results[region] = {
                "avg_latency": 0.0,
                "p95_latency": 0.0,
                "avg_uptime": 0.0,
                "breaches": 0
            }
            continue

        lats = [float(r['latency_ms']) for r in recs if 'latency_ms' in r]
        upts = [float(r['uptime_pct']) for r in recs if 'uptime_pct' in r]
        
        if not lats:
            results[region] = {"avg_latency": 0.0, "p95_latency": 0.0, "avg_uptime": 0.0, "breaches": 0}
            continue

        results[region] = {
            "avg_latency": round(sum(lats) / len(lats), 4),
            "p95_latency": round(float(calculate_p95(lats)), 4),
            "avg_uptime": round(sum(upts) / len(upts), 4),
            "breaches": sum(1 for l in lats if l > threshold)
        }

    return results