"""
Search for institutions by name via the Urban Institute IPEDS API.
Returns a list of {unitid, name, city, state} matches.
"""
import json
import urllib.request
from http.server import BaseHTTPRequestHandler

IPEDS_SEARCH = "https://educationdata.urban.org/api/v1/college-university/ipeds/institutional-characteristics/2023/?fields=unitid,inst_name,city,state_abbr&inst_name={query}&per_page=20"


def _search(query: str) -> list[dict]:
    url = IPEDS_SEARCH.format(query=urllib.parse.quote(query))
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read())
    results = data.get("results", [])
    return [
        {
            "unitid": r["unitid"],
            "name": r["inst_name"],
            "city": r["city"],
            "state": r["state_abbr"],
        }
        for r in results
    ]


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        import urllib.parse
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        query = params.get("q", [""])[0].strip()

        if not query:
            self._respond(400, {"error": "q parameter required"})
            return

        try:
            results = _search(query)
            self._respond(200, results)
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
