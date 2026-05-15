"""
Given a list of unitids, return pairwise comparisons of all shared numerical fields.
Each field gets a similarity bucket: identical | very_similar | similar | different | very_different | order_of_magnitude
"""
import json
import math
import os
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(__file__))
from school import _fetch_school

NON_NUMERIC = {"unitid", "inst_name", "city", "state_abbr", "sector", "hbcu", "tribal", "_labels"}

BUCKET_THRESHOLDS = [
    (0.00, "identical"),
    (0.05, "very similar"),
    (0.20, "similar"),
    (0.50, "different"),
    (0.90, "very different"),
    (10.0, "order of magnitude"),
]


def _bucket(a: float, b: float) -> str:
    if a == b:
        return "identical"
    lo, hi = min(a, b), max(a, b)
    if lo == 0:
        ratio = float("inf") if hi > 0 else 0.0
    else:
        ratio = (hi - lo) / lo
    for threshold, label in BUCKET_THRESHOLDS:
        if ratio <= threshold:
            return label
    return "order of magnitude"


def _compare_pair(data_a: dict, data_b: dict) -> list[dict]:
    labels = {**data_a.get("_labels", {}), **data_b.get("_labels", {})}
    numeric_keys = [
        k for k in set(data_a) | set(data_b)
        if k not in NON_NUMERIC
        and isinstance(data_a.get(k), (int, float))
        and isinstance(data_b.get(k), (int, float))
    ]
    rows = []
    for key in sorted(numeric_keys):
        va, vb = data_a[key], data_b[key]
        rows.append({
            "field": key,
            "label": labels.get(key, key),
            "a": va,
            "b": vb,
            "similarity": _bucket(float(va), float(vb)),
        })
    return rows


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        unitids = params.get("unitids", [""])[0].split(",")
        unitids = [u.strip() for u in unitids if u.strip()]

        if len(unitids) < 2 or len(unitids) > 5:
            self._respond(400, {"error": "Provide 2–5 unitids"})
            return

        try:
            schools = {uid: _fetch_school(uid) for uid in unitids}
        except Exception as exc:
            self._respond(500, {"error": str(exc)})
            return

        pairs = []
        uids = list(schools.keys())
        for i in range(len(uids)):
            for j in range(i + 1, len(uids)):
                a, b = uids[i], uids[j]
                pairs.append({
                    "school_a": {"unitid": a, "name": schools[a].get("inst_name", a)},
                    "school_b": {"unitid": b, "name": schools[b].get("inst_name", b)},
                    "comparisons": _compare_pair(schools[a], schools[b]),
                })

        self._respond(200, {"schools": list(schools.values()), "pairs": pairs})

    def _respond(self, status: int, body):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass
