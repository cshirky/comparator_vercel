#!/usr/bin/env python3
"""Local dev server. Serves public/ as static files and routes /api/* to handlers."""
import json
import mimetypes
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "api"))
from _school_data import fetch_school, FIELD_LABELS
from compare import _compare_pair

PUBLIC = Path(__file__).parent
PORT = int(os.environ.get("PORT", 3000))


class DevServer(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/api/school":
            self._handle_school(params)
        elif path == "/api/compare":
            self._handle_compare(params)
        else:
            self._static(path)

    def _handle_school(self, params):
        unitid = params.get("unitid", [""])[0].strip()
        if not unitid:
            return self._json(400, {"error": "unitid required"})
        try:
            data = fetch_school(unitid)
            data["_labels"] = FIELD_LABELS
            self._json(200, data)
        except Exception as exc:
            self._json(500, {"error": str(exc)})

    def _handle_compare(self, params):
        raw = params.get("unitids", [""])[0]
        unitids = [u.strip() for u in raw.split(",") if u.strip()]
        if not (2 <= len(unitids) <= 5):
            return self._json(400, {"error": "Provide 2–5 unitids"})
        try:
            schools = {uid: fetch_school(uid) for uid in unitids}
        except Exception as exc:
            return self._json(500, {"error": str(exc)})
        pairs = [
            {
                "school_a": {"unitid": a, "name": schools[a].get("inst_name", a)},
                "school_b": {"unitid": b, "name": schools[b].get("inst_name", b)},
                "comparisons": _compare_pair(schools[a], schools[b]),
            }
            for i, a in enumerate(unitids)
            for b in unitids[i + 1:]
        ]
        self._json(200, {"schools": list(schools.values()), "pairs": pairs})

    def _json(self, status, body):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def _static(self, path):
        if path in ("/", ""):
            path = "/index.html"
        file_path = PUBLIC / path.lstrip("/")
        if file_path.exists() and file_path.is_file():
            data = file_path.read_bytes()
            mime, _ = mimetypes.guess_type(str(file_path))
            self.send_response(200)
            self.send_header("Content-Type", mime or "application/octet-stream")
            self.end_headers()
            self.wfile.write(data)
        else:
            data = (PUBLIC / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(data)

    def log_message(self, fmt, *args):
        print(f"  {fmt % args}")


if __name__ == "__main__":
    server = HTTPServer(("localhost", PORT), DevServer)
    print(f"Dev server → http://localhost:{PORT}")
    server.serve_forever()
