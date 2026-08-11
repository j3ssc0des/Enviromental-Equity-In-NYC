#!/usr/bin/env python3
"""Fail CI when a generated site is incomplete, demo-backed, or misleading."""
import json, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data/processed/nta_environmental_snapshot.geojson"
HEAT_DATA=ROOT/"data/processed/nta2020_heat_vulnerability.geojson"
errors=[]
if not DATA.exists(): errors.append("processed GeoJSON is missing")
else:
    features=json.loads(DATA.read_text()).get("features",[])
    props=[f.get("properties",{}) for f in features]
    if len(features)<190: errors.append(f"expected at least 190 NTAs; found {len(features)}")
    if any(p.get("data_mode")!="official" for p in props): errors.append("demo data detected")
    if len({p.get("nta_code") for p in props}) != len(features): errors.append("duplicate NTA rows detected")
    if any(p.get("density_2005") is None for p in props): errors.append("NTA lacks derived 2005 tree density")
    if any(p.get("dataset_geography")!="NTA2010" or p.get("geography_vintage")!=2010 for p in props):
        errors.append("tree data are not on their native 2010 NTA geography")
    retired_fields={"median_income","income_coverage_pct","income_estimated","underserved",
                    "screening_score_method","investment_eligible","equity_label","pm25"}
    leaked_fields=sorted({key for p in props for key in p if key in retired_fields})
    if leaked_fields: errors.append(f"retired estimated/screening fields remain published: {leaked_fields}")
    if any("heat_proxy" in p or "heat_proxy_method" in p for p in props):
        errors.append("retired duplicate tree-and-income proxy remains in published data")
    tree_years={p.get("tree_source_year") for p in props}
    if tree_years != {2015}: errors.append(f"unexpected tree source years: {sorted(tree_years, key=str)}")
    history_coverage={p.get("tree_2005_mapping_coverage_pct") for p in props}
    if None in history_coverage or len(history_coverage)!=1:
        errors.append(f"2005 tree mapping coverage metadata is inconsistent: {history_coverage}")
    elif float(next(iter(history_coverage)))<95:
        errors.append(f"2005 tree mapping coverage is too low: {history_coverage}")
    if any(p.get("tree_2005_unassigned_count") is None for p in props):
        errors.append("2005 unassigned tree count metadata is missing")
if not HEAT_DATA.exists(): errors.append("official HVI GeoJSON is missing")
else:
    heat_features=json.loads(HEAT_DATA.read_text()).get("features",[])
    heat_props=[f.get("properties",{}) for f in heat_features]
    if len(heat_features)!=197: errors.append(f"expected 197 official HVI NTAs; found {len(heat_features)}")
    if len({p.get("nta_code") for p in heat_props})!=len(heat_features): errors.append("duplicate HVI NTA codes detected")
    if any(p.get("data_mode")!="official" for p in heat_props): errors.append("non-official HVI data detected")
    if any(p.get("dataset_geography")!="NTA2020" or p.get("geography_vintage")!=2020 for p in heat_props):
        errors.append("HVI geography is not native 2020 NTA")
    if any(p.get("hvi_source_year")!=2023 for p in heat_props): errors.append("unexpected HVI source year")
    if any(not isinstance(p.get("hvi_score"),int) or not 1<=p["hvi_score"]<=5 for p in heat_props):
        errors.append("HVI score is outside the official 1-5 range")
    if any("estimated" in key.lower() for p in heat_props for key in p):
        errors.append("estimated field appears in native HVI product")
html=(ROOT/"index.html").read_text()
for forbidden in (">LIVE<", "hazardous", "safe limit", "receive less investment",
                  "LOWER RISK", "NYC Healthy Benchmark", "investment_eligible !== false", "\u2014"):
    if forbidden.lower() in html.lower(): errors.append(f"unsupported UI language remains: {forbidden}")
for required in ("data/processed/nta_environmental_snapshot.geojson",
                 "data/processed/nta2020_heat_vulnerability.geojson",
                 "Official source geographies",
                 'id="download-report"', 'Download report',
                 'data-tab="heat"', 'NTA2020', 'Heat Vulnerability Index (2023)',
                 "select_at_location", "sourceGeography", "resolveReportRecord",
                 "COMBINED LOCATION REPORT", 'role="combobox"', "renderSearchSuggestions"):
    if required not in html: errors.append(f"required UI safeguard is missing: {required}")
pipeline=(ROOT/"nyc_trees_analysis.py").read_text()
for forbidden in ("Heat Risk:", "Urban Heat Vulnerability", "Underserved Index"):
    if forbidden in pipeline: errors.append(f"unsupported map language remains: {forbidden}")
interpretation=(ROOT/"assets/interpretation.mjs").read_text()
for required in ("buildInterpretation", "official 2023 Heat Vulnerability Index score",
                 "standard neighborhood NTAs", "borough’s area-weighted density",
                 "HVI-area median", "establish causation"):
    if required not in interpretation: errors.append(f"local interpretation safeguard is missing: {required}")
published_text=(ROOT/"index.html").read_text()+interpretation
for forbidden in ("OPENAI_API_KEY", "api.openai.com", "ATLAS_AI_ENDPOINT", "AI interpretation"):
    if forbidden.lower() in published_text.lower(): errors.append(f"remote AI dependency remains: {forbidden}")
if re.search(r"sk-[A-Za-z0-9_-]{16,}", published_text):
    errors.append("an API-key-like value appears in published source")
if errors:
    print("BUILD VALIDATION FAILED\n- "+"\n- ".join(errors)); sys.exit(1)
print("Build validation passed")
