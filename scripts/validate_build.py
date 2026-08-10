#!/usr/bin/env python3
"""Fail CI when a generated site is incomplete, demo-backed, or misleading."""
import json, re, sys
from datetime import datetime, timezone
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
    if any(p.get("density_2005") is None for p in props): errors.append("NTA lacks derived 2005 tree density")
    eligible_coverage=[p.get("income_coverage_pct",0) or 0 for p in eligible]
    if eligible_coverage and min(eligible_coverage)<90: errors.append(f"eligible income coverage below 90%: {min(eligible_coverage)}")
    nonres=[p for p in props if p.get("investment_eligible") is False]
    if not nonres: errors.append("non-residential/context areas were not classified")
    if any(p.get("underserved") is not None for p in nonres):
        errors.append("non-residential areas appear in screening-score comparisons")
    if any("heat_proxy" in p or "heat_proxy_method" in p for p in props):
        errors.append("retired duplicate tree-and-income proxy remains in published data")
    blocked_name=re.compile(r"airport|park-cemetery|cemetery|park$|riker|fort totten|governors island|ellis island|liberty island",re.I)
    leaked=[p.get("nta_name") for p in eligible if blocked_name.search(str(p.get("nta_name","")))]
    if leaked: errors.append(f"blocked context names appear in rankings: {leaked[:5]}")
    income_years=[int(p["income_source_year"]) for p in props if p.get("income_source_year") is not None]
    if not income_years: errors.append("income source year is missing")
    elif max(income_years) < datetime.now(timezone.utc).year-2:
        errors.append(f"ACS release is stale: latest source year {max(income_years)}")
    tree_years={p.get("tree_source_year") for p in props}
    if tree_years != {2015}: errors.append(f"unexpected tree source years: {sorted(tree_years, key=str)}")
    history_coverage={p.get("tree_2005_mapping_coverage_pct") for p in props}
    if None in history_coverage or len(history_coverage)!=1:
        errors.append(f"2005 tree mapping coverage metadata is inconsistent: {history_coverage}")
    elif float(next(iter(history_coverage)))<95:
        errors.append(f"2005 tree mapping coverage is too low: {history_coverage}")
    if any(p.get("tree_2005_unassigned_count") is None for p in props):
        errors.append("2005 unassigned tree count metadata is missing")
html=(ROOT/"index.html").read_text()
for forbidden in (">LIVE<", "hazardous", "safe limit", "receive less investment",
                  "LOWER RISK", "NYC Healthy Benchmark", "investment_eligible !== false", "\u2014"):
    if forbidden.lower() in html.lower(): errors.append(f"unsupported UI language remains: {forbidden}")
for required in ("data/processed/nta_environmental_snapshot.geojson",
                 "investment_eligible === true", "NON_RESIDENTIAL_NAME",
                 "Rankings are hidden rather than showing stale values"):
    if required not in html: errors.append(f"required UI safeguard is missing: {required}")
pipeline=(ROOT/"nyc_trees_analysis.py").read_text()
for forbidden in ("Heat Risk:", "Urban Heat Vulnerability", "Underserved Index"):
    if forbidden in pipeline: errors.append(f"unsupported map language remains: {forbidden}")
interpretation=(ROOT/"assets/interpretation.mjs").read_text()
for required in ("buildInterpretation", "investment_eligible !== true", "not to make a funding decision"):
    if required not in interpretation: errors.append(f"local interpretation safeguard is missing: {required}")
published_text=(ROOT/"index.html").read_text()+interpretation
for forbidden in ("OPENAI_API_KEY", "api.openai.com", "ATLAS_AI_ENDPOINT", "AI interpretation"):
    if forbidden.lower() in published_text.lower(): errors.append(f"remote AI dependency remains: {forbidden}")
if re.search(r"sk-[A-Za-z0-9_-]{16,}", published_text):
    errors.append("an API-key-like value appears in published source")
if errors:
    print("BUILD VALIDATION FAILED\n- "+"\n- ".join(errors)); sys.exit(1)
print("Build validation passed")
