#!/usr/bin/env python3
"""Audit declared public data sources and write a machine-readable report."""
import json, os, subprocess, sys, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SOURCES = ROOT / "data" / "sources.json"
REPORT = ROOT / "data" / "metadata" / "source-audit.json"

def get_json(url):
    result=subprocess.run(["curl","-fsSL","--max-time","45","-A","nyc-environmental-atlas-audit/1.0",url],
                          check=True,capture_output=True,text=True)
    return json.loads(result.stdout)

def audit(source):
    if source["kind"] == "socrata":
        url = f"https://data.cityofnewyork.us/resource/{source['id']}.json?$limit=1"
        payload=get_json(url)
    else:
        variables = ",".join(source["required_fields"])
        query=urllib.parse.urlencode([
            ("get",f"NAME,{variables}"),("for","tract:*"),
            ("in","state:36"),("in","county:061"),
        ] + ([("key",os.environ["CENSUS_API_KEY"])] if os.getenv("CENSUS_API_KEY") else []))
        url = "https://api.census.gov/data/2015/acs/acs5?"+query
        payload=get_json(url)
    fields = set(payload[0] if source["kind"] == "census" else (payload[0] if payload else {}))
    missing = sorted(set(source["required_fields"]) - fields)
    return {"id":source["id"], "name":source["name"], "status":source["status"],
            "reachable":True, "missing_required_fields":missing, "ok":not missing, "checked_url":url}

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
