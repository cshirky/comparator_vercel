"""Shared school data fetching and caching logic."""
import json
import os
import urllib.request

CACHE_DIR = "/tmp/school_cache"
BASE = "https://educationdata.urban.org/api/v1/college-university/ipeds"

FIELD_LABELS = {
    "applications": "Applications received",
    "admissions": "Students admitted",
    "admit_rate": "Admission rate",
    "enrolled_ft": "Enrolled full-time",
    "enrolled_total": "Enrolled (total)",
    "tuition_in_state": "Tuition & fees (in-state)",
    "tuition_out_of_state": "Tuition & fees (out-of-state)",
    "room_board": "Room & board",
    "grad_rate_6yr": "6-year graduation rate",
    "grad_cohort_size": "Graduation cohort size",
    "hbcu": "HBCU",
    "tribal": "Tribal college",
    "sector": "Sector",
}


def _get(url: str) -> list[dict]:
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read()).get("results", [])


def fetch_school(unitid: str) -> dict:
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{unitid}.json")
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            return json.load(f)

    out = {"unitid": int(unitid)}

    rows = _get(f"{BASE}/directory/2023/?unitid={unitid}")
    if rows:
        r = rows[0]
        out.update({
            "inst_name": r.get("inst_name"),
            "city": r.get("city"),
            "state": r.get("state_abbr"),
            "sector": r.get("sector"),
            "hbcu": r.get("hbcu"),
            "tribal": r.get("tribal_college"),
        })

    rows = _get(f"{BASE}/admissions-enrollment/2022/?unitid={unitid}")
    total = next((r for r in rows if r.get("sex") == 99), None)
    if total:
        applied = total.get("number_applied") or 0
        admitted = total.get("number_admitted") or 0
        out["applications"] = applied
        out["admissions"] = admitted
        out["admit_rate"] = round(admitted / applied, 4) if applied else None
        out["enrolled_ft"] = total.get("number_enrolled_ft")
        out["enrolled_total"] = total.get("number_enrolled_total")

    rows = _get(f"{BASE}/academic-year-tuition/2021/?unitid={unitid}&level_of_study=1")
    for r in rows:
        t = r.get("tuition_type")
        if t == 2:
            out["tuition_in_state"] = r.get("tuition_fees_published")
        elif t == 3:
            out["tuition_out_of_state"] = r.get("tuition_fees_published")
        elif t == 5:
            out["room_board"] = r.get("tuition_fees_published")

    rows = _get(f"{BASE}/grad-rates/2022/?unitid={unitid}&subcohort=2&race=99&sex=99")
    grad = next((r for r in rows if r.get("completion_rate_150pct") is not None), None)
    if grad:
        out["grad_rate_6yr"] = grad.get("completion_rate_150pct")
        out["grad_cohort_size"] = grad.get("cohort_adj_150pct")

    with open(cache_path, "w") as f:
        json.dump(out, f)
    return out
