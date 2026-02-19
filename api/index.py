import json
import os
from http.server import BaseHTTPRequestHandler

# Load telemetry data
telemetry = []
_data_path = os.path.join(os.path.dirname(__file__), "telemetry.json")
if os.path.exists(_data_path):
    try:
        with open(_data_path, "r") as f:
            telemetry = json.load(f)
    except:
        pass

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "records": len(telemetry)}).encode())

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                body = {}
            else:
                post_data = self.rfile.read(content_length)
                body = json.loads(post_data)
        except:
            body = {}

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

            latencies = sorted([float(r.get("latency_ms", 0)) for r in region_data])
            uptimes = [float(r.get("uptime_pct", 0)) for r in region_data]

            # P95 calculation
            p95_idx = int(0.95 * len(latencies))
            p95_val = latencies[min(p95_idx, len(latencies) - 1)]

            results[region] = {
                "avg_latency": round(sum(latencies) / len(latencies), 4),
                "p95_latency": round(float(p95_val), 4),
                "avg_uptime": round(sum(uptimes) / len(uptimes), 4),
                "breaches": sum(1 for l in latencies if l > threshold_ms)
            }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(results).encode())