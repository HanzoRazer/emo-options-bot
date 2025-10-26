from http.server import BaseHTTPRequestHandler, HTTPServer
import json, threading, time, os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from utils.enhanced_config import Config

_state = {"status":"boot","cycle":0,"metrics":{}}

def snapshot(perf, latest_files=None):
    _state["status"] = "ok"
    _state["cycle"] = len(perf.get("cycle_times", []))
    _state["metrics"] = perf
    if latest_files:
        _state["latest"] = latest_files

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        b = json.dumps(obj, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def do_GET(self):
        if self.path.startswith("/health"):
            self._send(200, {"status":_state["status"], "cycle":_state["cycle"]})
        elif self.path.startswith("/metrics"):
            # optionally merge file metrics if present
            metrics_file = Path("data/metrics.json")
            merged = dict(_state)
            if metrics_file.exists():
                try:
                    merged["file_metrics"] = json.loads(metrics_file.read_text())
                except Exception as e:
                    merged["file_metrics_error"] = str(e)
            self._send(200, merged)
        else:
            self._send(404, {"error":"not found"})

def serve(port=8082):
    srv = HTTPServer(("0.0.0.0", port), H)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return t

if __name__ == "__main__":
    cfg = Config()
    port = int(cfg.get("HEALTH_PORT", "8082"))
    print(f"[health] Serving on 0.0.0.0:{port}")
    serve(port)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[health] Stopped.")