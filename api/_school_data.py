"""
School data from pre-built IPEDS dataset (institutions.csv vintage 2023).
Loaded once at cold-start from api/school_data.json; no external API calls.
"""
import json
import os

_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "school_data.json")
_DB: dict | None = None


def _db() -> dict:
    global _DB
    if _DB is None:
        with open(_DATA_PATH) as f:
            _DB = json.load(f)
    return _DB


FIELD_LABELS = {
    "admission_rate":      "Admission rate",
    "grad_rate_6yr":       "6-year graduation rate",
    "completion_rate_8yr": "8-year completion rate",
    "enrollment_total":    "Total enrollment",
    "enrollment_ug":       "Undergraduate enrollment",
    "pct_women":           "% women",
    "pct_white":           "% white",
    "pct_black":           "% Black",
    "pct_hispanic":        "% Hispanic",
    "pct_asian":           "% Asian",
    "pct_federal_loan":    "% federal loan recipients",
    "tuition_in_state":    "Tuition & fees (in-state)",
    "tuition_out_of_state":"Tuition & fees (out-of-state)",
    "net_price":           "Average net price",
    "grad_debt_median":    "Median graduate debt",
    "sat_avg":             "SAT average",
    "act_avg":             "ACT average",
    "yield_rate":          "Yield rate",
    "ug_pct_parttime":     "% undergrads part-time",
    "ug_pct_age_24_under": "% undergrads age 24 and under",
    "ug_pct_instate":      "% undergrads in-state",
    "ug_pct_foreign":      "% undergrads from foreign countries",
    "ug_pct_distance":     "% undergrads distance-only enrollment",
}


def fetch_school(unitid: str) -> dict:
    db = _db()
    record = db.get(str(unitid))
    if record is None:
        return {"unitid": int(unitid), "inst_name": f"Unknown ({unitid})", "error": "not in dataset"}
    return dict(record)
