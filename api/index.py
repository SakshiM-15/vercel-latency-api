from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Access-Control-Allow-Origin"],
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(CURRENT_DIR, "q-vercel-latency.json")

def calculate_xo(values, a):
    sorted_values = sorted(values)
    i = (len(sorted_values) - 1) * a
    s = int(i)
    h = i - s
    if s + 1 < len(sorted_values):
        return sorted_values[s] + h * (sorted_values[s+1] - sorted_values[s])
    return sorted_values[s]

@app.get("/api")
@app.get("/")
async def health():
    return {"status": "ok"}

@app.post("/api")
@app.post("/")
async def process_latency(request: Request):
    try:
        if not os.path.exists(DATA_FILE):
             return {"error": f"File not found at {DATA_FILE}"}
             
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            
        body = await request.json()
        req_regions = body.get("regions", [])
        threshold = body.get("threshold_ms", 180)
        
        results = []
        for r_name in req_regions:
            region_data = [d for d in data if d["region"] == r_name]
            if not region_data: continue
                
            latencies = [d["latency_ms"] for d in region_data]
            uptimes = [d["uptime_pct"] for d in region_data]
            
            avg_latency = sum(latencies) / len(latencies)
            p95_latency = calculate_xo(latencies, 0.95)
            avg_uptime = sum(uptimes) / len(uptimes)
            breaches = sum(1 for l in latencies if l > threshold)
            
            results.append({
                "region": r_name,
                "avg_latency": float(f"{avg_latency:.2f}"),
                "p95_latency": float(f"{p95_latency:.2f}"),
                "avg_uptime": float(f"{avg_uptime:.3f}"),
                "breaches": breaches
            })
        return {"regions": results}
    except Exception as e:
        return {"error": str(e)}

# Handle OPTIONS request manually just in case middleware is bypassed
@app.options("/api")
@app.options("/")
async def options_handler():
    return {}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)