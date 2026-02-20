import json
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# Load telemetry data
TELEMETRY = []
_data_path = os.path.join(os.path.dirname(__file__), "telemetry.json")
if os.path.exists(_data_path):
    with open(_data_path, "r") as f:
        TELEMETRY = json.load(f)

def calculate_p95(lats):
    if not lats: return 0.0
    sorted_lats = sorted(lats)
    n = len(sorted_lats)
    idx = int(0.95 * n)
    return sorted_lats[min(idx, n - 1)]

@app.get("/")
@app.get("/api")
@app.get("/health")
async def health():
    return {"status": "ok", "records": len(TELEMETRY), "message": "Latency API is running"}

@app.post("/")
@app.post("/api")
async def analytics(request: Request):
    try:
        data = await request.json()
    except:
        return {"error": "Invalid JSON"}
    
    regions = data.get("regions", [])
    threshold = data.get("threshold_ms", 180)
    
    results = {}
    for region_name in regions:
        # Case-insensitive filtering
        recs = [r for r in TELEMETRY if str(r.get("region", "")).lower() == region_name.lower()]
        
        if not recs:
            results[region_name] = {
                "avg_latency": 0.0,
                "p95_latency": 0.0,
                "avg_uptime": 0.0,
                "breaches": 0
            }
            continue
            
        latencies = [float(r['latency_ms']) for r in recs if 'latency_ms' in r]
        uptimes = [float(r['uptime_pct']) for r in recs if 'uptime_pct' in r]
        
        if not latencies:
            results[region_name] = {"avg_latency": 0.0, "p95_latency": 0.0, "avg_uptime": 0.0, "breaches": 0}
            continue
            
        results[region_name] = {
            "avg_latency": round(sum(latencies) / len(latencies), 4),
            "p95_latency": round(calculate_p95(latencies), 4),
            "avg_uptime": round(sum(uptimes) / len(uptimes), 4),
            "breaches": sum(1 for l in latencies if l > threshold)
        }
        
    return results