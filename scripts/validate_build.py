#!/usr/bin/env python3
"""Fail CI when a generated site is incomplete, demo-backed, or misleading."""
import json, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/processed/nta_environmental_snapshot.geojson"
errors=[]
if not DATA.exists(): errors.append("processed GeoJSON is missing")
else:
    features=json.loads(DATA.read_text()).get("features",[])
    props=[f.get("properties",{}) for f in features]
    if len(features)<190: errors.append(f"expected at least 190 NTAs; found {len(features)}")
    if any(p.get("data_mode")!="official" for p in props): errors.append("demo data detected")
    if len({p.get("nta_code") for p in props}) != len(features): errors.append("duplicate NTA rows detected")
    incomes=[p.get("median_income") for p in props]
    if len({v for v in incomes if v is not None})<100: errors.append("income values show suspiciously low diversity")
    coverage=[p.get("income_coverage_pct",0) or 0 for p in props]
    eligible=[p for p in props if p.get("investment_eligible") is True]
    if not eligible: errors.append("no investment-eligible residential NTAs found")
    if any(p.get("median_income") is None for p in eligible): errors.append("eligible NTA lacks income")
    eligible_coverage=[p.get("income_coverage_pct",0) or 0 for p in eligible]
    if eligible_coverage and min(eligible_coverage)<90: errors.append(f"eligible income coverage below 90%: {min(eligible_coverage)}")
    nonres=[p for p in props if p.get("investment_eligible") is False]
    if not nonres: errors.append("non-residential/context areas were not classified")
    if any(p.get("underserved") is not None or p.get("heat_proxy") is not None for p in nonres):
        errors.append("non-residential areas appear in investment or heat-proxy scoring")
html=(ROOT/"index.html").read_text()
for forbidden in (">LIVE<", "hazardous", "safe limit", "receive less investment"):
    if forbidden.lower() in html.lower(): errors.append(f"unsupported UI language remains: {forbidden}")
if errors:
    print("BUILD VALIDATION FAILED\n- "+"\n- ".join(errors)); sys.exit(1)
print("Build validation passed")
