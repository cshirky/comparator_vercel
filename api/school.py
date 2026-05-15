"""
Fetch numerical characteristics for a single institution from IPEDS.
Caches results in /tmp keyed by unitid.
"""
import json
import os
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler

CACHE_DIR = "/tmp/school_cache"

ENDPOINTS = {
    "admissions": "https://educationdata.urban.org/api/v1/college-university/ipeds/admissions-requirements/2023/?unitid={unitid}&fields=unitid,applcn,admssn,enrlt,satvr25,satvr75,satmt25,satmt75,actcm25,actcm75",
    "enrollment": "https://educationdata.urban.org/api/v1/college-university/ipeds/fall-enrollment/2023/?unitid={unitid}&fields=unitid,efytotlt,efytotlm,efytotlw",
    "graduation": "https://educationdata.urban.org/api/v1/college-university/ipeds/grad-rates/2023/?unitid={unitid}&fields=unitid,grtotlt,grtotlm,grtotlw",
    "finance": "https://educationdata.urban.org/api/v1/college-university/ipeds/student-financial-aid/2023/?unitid={unitid}&fields=unitid,scugffn,scugffp,anyaidp,fedloanp",
    "characteristics": "https://educationdata.urban.org/api/v1/college-university/ipeds/institutional-characteristics/2023/?unitid={unitid}&fields=unitid,inst_name,city,state_abbr,sector,hbcu,tribal,longitud,latitude,tuition1,tuition2,tuition3,tuition4,roomboard,fte12mn",
}

FIELD_LABELS = {
    "applcn": "Applications received",
    "admssn": "Admissions",
    "enrlt": "Enrolled (full-time first-time)",
    "satvr25": "SAT verbal 25th pct",
    "satvr75": "SAT verbal 75th pct",
    "satmt25": "SAT math 25th pct",
    "satmt75": "SAT math 75th pct",
    "actcm25": "ACT composite 25th pct",
    "actcm75": "ACT composite 75th pct",
    "efytotlt": "Total enrollment",
    "efytotlm": "Total enrollment (men)",
    "efytotlw": "Total enrollment (women)",
    "grtotlt": "6-yr graduation rate (total)",
    "grtotlm": "6-yr graduation rate (men)",
    "grtotlw": "6-yr graduation rate (women)",
    "scugffn": "Students receiving aid (n)",
    "scugffp": "Students receiving aid (%)",
    "anyaidp": "Any financial aid (%)",
    "fedloanp": "Federal loan (%)",
    "tuition1": "Tuition in-district",
    "tuition2": "Tuition in-state",
    "tuition3": "Tuition out-of-state",
    "tuition4": "Tuition out-of-state (2)",
    "roomboard": "Room & board",
    "fte12mn": "FTE enrollment (12-month)",
    "longitud": "Longitude",
    "latitude": "Latitude",
}


def _fetch_endpoint(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read())
    results = data.get("results", [])
    return results[0] if results else {}


def _fetch_school(unitid: str) -> dict:
    cache_path = os.path.join(CACHE_DIR, f"{unitid}.json")
    os.makedirs(CACHE_DIR, exist_ok=True)

    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)

    merged = {}
    for key, url_template in ENDPOINTS.items():
        url = url_template.format(unitid=unitid)
        try:
            record = _fetch_endpoint(url)
            merged.update(record)
        except Exception:
            pass

    # Keep only numerical fields plus identifiers
    NON_NUMERIC = {"unitid", "inst_name", "city", "state_abbr", "sector", "hbcu", "tribal"}
    numerics = {
        k: v for k, v in merged.items()
        if k in NON_NUMERIC or (isinstance(v, (int, float)) and v is not None)
    }
    numerics["_labels"] = {k: FIELD_LABELS.get(k, k) for k in numerics if k not in NON_NUMERIC and k != "_labels"}

    with open(cache_path, "w") as f:
        json.dump(numerics, f)

    return numerics


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        unitid = params.get("unitid", [""])[0].strip()

        if not unitid:
            self._respond(400, {"error": "unitid parameter required"})
            return

        try:
            data = _fetch_school(unitid)
            self._respond(200, data)
        except Exception as exc:
            self._respond(500, {"error": str(exc)})

    def _respond(self, status: int, body):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass
