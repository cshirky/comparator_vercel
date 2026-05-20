import json
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _school_data import fetch_school, FIELD_LABELS

IDENTITY_KEYS = {"unitid", "inst_name", "city", "state", "sector", "hbcu", "tribal", "_labels"}

BUCKETS = [
    (0.0,  "identical"),
    (0.05, "very similar"),
    (0.20, "similar"),
    (0.50, "different"),
    (0.90, "very different"),
]


def _bucket(a: float, b: float) -> str:
    if a == b:
        return "identical"
    lo, hi = min(a, b), max(a, b)
    ratio = (hi - lo) / lo if lo != 0 else float("inf")
    for threshold, label in BUCKETS:
        if ratio <= threshold:
            return label
    return "order of magnitude"


def _compare_pair(a: dict, b: dict) -> list[dict]:
    numeric_keys = sorted(
        k for k in set(a) | set(b)
        if k not in IDENTITY_KEYS
        and isinstance(a.get(k), (int, float))
        and isinstance(b.get(k), (int, float))
    )
    return [
        {
            "field": k,
            "label": FIELD_LABELS.get(k, k),
            "a": a[k],
            "b": b[k],
            "similarity": _bucket(float(a[k]), float(b[k])),
        }
        for k in numeric_keys
    ]


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
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

    def log_message(self, *args):
        pass
