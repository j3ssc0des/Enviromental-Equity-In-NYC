#!/usr/bin/env python3
"""Audit declared public data sources and write a machine-readable report."""
import csv, io, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SOURCES = ROOT / "data" / "sources.json"
REPORT = ROOT / "data" / "metadata" / "source-audit.json"
ACS_CACHE = ROOT / "data" / "raw" / "acs_income.json"

def get_json(url):
    result=subprocess.run(["curl","-fsSL","--max-time","45","-A","nyc-environmental-atlas-audit/1.0",url],
                          check=True,capture_output=True,text=True)
    return json.loads(result.stdout)

def get_text(url):
    result=subprocess.run(["curl","-fsSL","--max-time","45","-A","nyc-environmental-atlas-audit/1.0",url],
                          check=True,capture_output=True,text=True)
    return result.stdout

def audit(source):
    observed_reference_year=None
    reference_period=None
    if source["kind"] == "socrata":
        url = f"https://data.cityofnewyork.us/resource/{source['id']}.json?$limit=1"
        payload=get_json(url)
    elif source["kind"] == "static_csv":
        url=source["url"]
        payload=list(csv.DictReader(io.StringIO(get_text(url))))
    else:
        url=("https://api.censusreporter.org/1.0/data/show/latest?"
             "table_ids=B19013%2CB11001&geo_ids=140%7C04000US36")
        payload=get_json(url)
    if source["kind"]=="census_reporter":
        if source["status"]=="active":
            ACS_CACHE.parent.mkdir(parents=True, exist_ok=True)
            ACS_CACHE.write_text(json.dumps(payload)+"\n")
        reference_period=str(payload["release"]["years"])
        observed_reference_year=int(reference_period.split("-")[-1])
        sample=next(iter(payload["data"].values()))
        fields=set(sample["B19013"]["estimate"])|set(sample["B11001"]["estimate"])
    else:
        fields=set(payload[0] if payload else {})
    missing = sorted(set(source["required_fields"]) - fields)
    max_lag=source.get("max_reference_lag_years")
    stale=bool(max_lag is not None and observed_reference_year is not None and
               datetime.now(timezone.utc).year-observed_reference_year>max_lag)
    return {"id":source["id"], "name":source["name"], "status":source["status"],
            "reachable":True, "missing_required_fields":missing, "stale":stale,
            "reference_period":reference_period, "observed_reference_year":observed_reference_year,
            "ok":not missing and not stale, "checked_url":url}

def main():
    results=[]
    for source in json.loads(SOURCES.read_text()):
        try: results.append(audit(source))
        except Exception as exc:
            results.append({"id":source["id"], "name":source["name"], "status":source["status"],
                            "reachable":False, "ok":False, "error":str(exc)})
    failures=[row for row in results if row["status"]=="active" and not row["ok"]]
    report={"checked_at":datetime.now(timezone.utc).isoformat(), "ok":not failures,
            "active_failures":len(failures), "sources":results}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return 1 if failures else 0

if __name__ == "__main__": sys.exit(main())
