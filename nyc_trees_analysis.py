

#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║   NYC STREET TREE CENSUS  ·  Green Space Inequity Analysis       ║
║   Data: NYC Open Data 2005 & 2015 Street Tree Census             ║
║   Tools: Python · Pandas · GeoPandas · Folium                    ║
╚══════════════════════════════════════════════════════════════════╝

The build uses declared official/public sources and fails closed when any
required source is unavailable.

OUTPUT: nyc_trees_map.html  (interactive Folium choropleth map)
"""

import warnings, json, io, time, os
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import folium
from folium import GeoJson, LayerControl
from folium.plugins import HeatMap
from branca.colormap import StepColormap
from branca.element import Element
import geopandas as gpd
warnings.filterwarnings("ignore")

# ────────────────────────────────────────────────────────────────
OUTPUT_HTML = "nyc_trees_map.html"
OUTPUT_DATA = "data/processed/nta_environmental_snapshot.geojson"
OUTPUT_HEAT_DATA = "data/processed/nta2020_heat_vulnerability.geojson"
OUTPUT_FLOOD_DATA = "data/processed/census_tract_flood_vulnerability.geojson"
# ────────────────────────────────────────────────────────────────

print("=" * 65)
print("  🌳  NYC Green Space Inequity: Street Tree Census Analysis")
print("=" * 65)


# ════════════════════════════════════════════════════════════════
# 1.  OFFICIAL DATA
# ════════════════════════════════════════════════════════════════

# ── Retry helper ─────────────────────────────────────────────────────────
def _fetch(url, params=None, max_retries=3, timeout=40):
    """GET with exponential-backoff retry. Raises on final failure."""
    import requests
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as exc:
            if attempt == max_retries:
                raise
            delay = 2 ** attempt
            print(f"   ⚠ Attempt {attempt}/{max_retries} failed: {exc}")
            print(f"     Retrying in {delay}s…")
            time.sleep(delay)

def _assert_unique_nta(frame, stage):
    duplicates=frame.loc[frame["nta_code"].duplicated(keep=False),"nta_code"].dropna().unique()
    if len(duplicates):
        raise ValueError(f"Duplicate NTA codes after {stage}: {sorted(duplicates.tolist())}")

# ── Official source fetch ─────────────────────────────────────────────────
live_ok = False
tree_2005_unassigned_count = 0
tree_2005_mapping_coverage_pct = 100.0
heat_gdf = None
flood_gdf = None

try:
    import requests

    print("\n📡 Fetching 2015 tree census from NYC Open Data…")
    r = _fetch(
        "https://data.cityofnewyork.us/resource/uvpi-gqnh.json",
        params={"$select": "nta,COUNT(*) as trees",
                "$group":  "nta",
                "$where":  "nta IS NOT NULL",
                "$limit":  "500"},
    )
    df15 = pd.DataFrame(r.json())
    df15 = df15.rename(columns={"nta": "nta_code"})
    df15["nta_code"] = df15["nta_code"].astype(str).str.strip()
    df15["trees_2015"] = pd.to_numeric(df15["trees"], errors="coerce").fillna(0).astype(int)
    df15 = df15[df15["nta_code"] != ""].copy()
    df15 = df15[["nta_code", "trees_2015"]]
    print(f"   ✓ {df15['trees_2015'].sum():,.0f} trees · {len(df15)} NTAs")

    print("📡 Fetching 2005 tree census from NYC Open Data…")
    r = _fetch(
        "https://data.cityofnewyork.us/resource/29bw-z7pj.json",
        params={"$select": "nta,COUNT(*) as trees",
                "$group":  "nta",
                "$where":  "nta IS NOT NULL",
                "$limit":  "500"},
    )
    df05 = pd.DataFrame(r.json())
    df05 = df05.rename(columns={"nta":"nta_code"})
    df05["nta_code"] = df05["nta_code"].astype(str).str.strip()
    df05["trees_2005"] = pd.to_numeric(df05["trees"], errors="coerce").fillna(0).astype(int)
    tree_2005_unassigned_count = int(df05.loc[df05["nta_code"] == "", "trees_2005"].sum())
    tree_2005_total = int(df05["trees_2005"].sum())
    df05 = df05[df05["nta_code"] != ""].copy()
    tree_2005_mapping_coverage_pct = round(
        100 * int(df05["trees_2005"].sum()) / tree_2005_total, 1
    ) if tree_2005_total else 0.0
    df05 = df05[["nta_code", "trees_2005"]]
    print(f"   ✓ {df05['trees_2005'].sum():,.0f} mapped trees · {len(df05)} NTAs")
    print(f"   ℹ {tree_2005_unassigned_count:,} records have blank NTA codes; "
          f"mapping coverage {tree_2005_mapping_coverage_pct:.1f}%")

    print("📡 Fetching 2010 census tract boundaries from US Census Bureau…")
    gdf_tracts = gpd.read_file(
        "https://www2.census.gov/geo/tiger/GENZ2010/gz_2010_36_140_00_500k.zip"
    )
    gdf_tracts = gdf_tracts.to_crs("EPSG:4326")
    nyc_counties = {"005", "047", "061", "081", "085"}
    gdf_tracts = gdf_tracts[
        gdf_tracts["COUNTY"].astype(str).str.zfill(3).isin(nyc_counties)
    ].copy()
    gdf_tracts["COUNTY"] = gdf_tracts["COUNTY"].astype(str).str.zfill(3)
    gdf_tracts["TRACT"]  = gdf_tracts["TRACT"].astype(str).str.zfill(6)
    print(f"   ✓ {len(gdf_tracts)} NYC census tracts loaded")

    print("📡 Fetching NTA crosswalk from NYC Open Data…")
    r = _fetch(
        "https://data.cityofnewyork.us/resource/8ius-dhrr.json",
        params={"$limit": "3000"},
    )
    xwalk = pd.DataFrame(r.json()).rename(columns={
        "_2010_census_tract":                    "TRACT",
        "_2010_census_bureau_fips_county_code":  "COUNTY",
        "neighborhood_tabulation_area_nta_code": "nta_code",
        "neighborhood_tabulation_area_nta_name": "nta_name",
        "borough":                               "boro_name",
    })
    xwalk["COUNTY"] = xwalk["COUNTY"].astype(str).str.zfill(3)
    xwalk["TRACT"]  = xwalk["TRACT"].astype(str).str.zfill(6)
    xwalk = xwalk[["TRACT","COUNTY","nta_code","nta_name","boro_name"]].drop_duplicates()
    print(f"   ✓ {len(xwalk)} crosswalk rows · {xwalk['nta_code'].nunique()} NTAs")

    gdf_with_nta = gdf_tracts.merge(xwalk, on=["TRACT","COUNTY"], how="left")
    gdf_with_nta = gdf_with_nta.dropna(subset=["nta_code"])
    if "CENSUSAREA" not in gdf_with_nta.columns:
        raise ValueError("2010 tract boundaries are missing required CENSUSAREA land-area field")
    gdf_with_nta["land_km2"] = pd.to_numeric(
        gdf_with_nta["CENSUSAREA"], errors="coerce"
    ) * 2.589988110336
    nta_land = gdf_with_nta.groupby("nta_code", as_index=False)["land_km2"].sum(min_count=1)
    gdf_boundaries = gdf_with_nta.drop(columns=["land_km2"]).dissolve(
        by="nta_code", aggfunc="first"
    ).reset_index()
    gdf_boundaries = gdf_boundaries.merge(nta_land, on="nta_code", how="left")
    gdf_boundaries = gdf_boundaries.set_crs("EPSG:4326", allow_override=True)
    _assert_unique_nta(gdf_boundaries,"boundary assembly")
    print(f"   ✓ {len(gdf_boundaries)} NTA polygons assembled")

    # Merge tree counts onto real boundary polygons
    # 2015: join directly on the NTA code (for example, "BX31")
    merged = gdf_boundaries.merge(df15, on="nta_code", how="left")
    # 2005 also supplies the stable 2010 NTA code.
    merged = merged.merge(df05, on="nta_code", how="left")
    _assert_unique_nta(merged,"tree census joins")
    merged["trees_2015"] = merged["trees_2015"].fillna(0).astype(int)
    merged["trees_2005"] = merged["trees_2005"].fillna(0).astype(int)

    # Census TIGER land area excludes water and is already measured in m².
    merged["area_km2"] = merged["land_km2"].round(2).clip(lower=0.1)

    # Centroid lat/lon for circle markers
    cents = merged.to_crs("EPSG:2263").geometry.centroid.to_crs("EPSG:4326")
    merged["lat"] = cents.y.round(4)
    merged["lon"] = cents.x.round(4)

    merged = gpd.GeoDataFrame(merged, geometry="geometry", crs="EPSG:4326")

    print("📡 Fetching official 2023 Heat Vulnerability Index on 2020 NTAs…")
    hvi_response = _fetch(
        "https://a816-dohbesp.nyc.gov/IndicatorPublic/data-features/hvi/hvi-nta-2020.csv"
    )
    hvi = pd.read_csv(io.StringIO(hvi_response.text), dtype=str)
    hvi_fields = [
        "NTACode", "GEONAME", "HVI_RANK", "SURFACE_TEMP", "GREENSPACE",
        "PCT_HOUSEHOLDS_AC",
    ]
    missing_hvi_fields = sorted(set(hvi_fields) - set(hvi.columns))
    if missing_hvi_fields:
        raise ValueError(f"Official HVI file is missing fields: {missing_hvi_fields}")
    duplicate_hvi = hvi[hvi["NTACode"].duplicated(keep=False)]
    for nta_code, group in duplicate_hvi.groupby("NTACode"):
        if len(group[hvi_fields].drop_duplicates()) != 1:
            raise ValueError(f"Conflicting official HVI rows for {nta_code}")
    hvi = hvi[hvi_fields].drop_duplicates(subset=["NTACode"]).copy()

    nta2020_response = _fetch(
        "https://data.cityofnewyork.us/resource/9nt8-h7nd.geojson",
        params={"$limit": "500"},
    )
    nta2020_payload = nta2020_response.json()
    nta2020 = gpd.GeoDataFrame.from_features(
        nta2020_payload.get("features", []), crs="EPSG:4326"
    )
    required_nta2020 = {"nta2020", "ntaname", "boroname", "geometry"}
    if not required_nta2020.issubset(nta2020.columns):
        raise ValueError("Official 2020 NTA boundaries are missing required fields")
    heat_gdf = nta2020.merge(hvi, left_on="nta2020", right_on="NTACode", how="inner")
    if len(heat_gdf) != len(hvi) or len(heat_gdf) < 190:
        raise ValueError(
            f"Official HVI geometry join is incomplete: {len(heat_gdf)}/{len(hvi)} rows"
        )
    heat_gdf["hvi_score"] = pd.to_numeric(heat_gdf["HVI_RANK"], errors="raise").astype(int)
    if not heat_gdf["hvi_score"].between(1, 5).all():
        raise ValueError("Official HVI scores fall outside the published 1–5 range")
    pd.to_numeric(heat_gdf["SURFACE_TEMP"], errors="raise")
    pd.to_numeric(heat_gdf["GREENSPACE"], errors="raise")
    pd.to_numeric(heat_gdf["PCT_HOUSEHOLDS_AC"], errors="raise")
    heat_gdf["surface_temp_f"] = heat_gdf["SURFACE_TEMP"]
    heat_gdf["greenspace_pct"] = heat_gdf["GREENSPACE"]
    heat_gdf["households_ac_pct"] = heat_gdf["PCT_HOUSEHOLDS_AC"]
    heat_gdf["nta_code"] = heat_gdf["NTACode"]
    heat_gdf["nta_name"] = heat_gdf["GEONAME"]
    heat_gdf["boro_name"] = heat_gdf["boroname"]
    heat_gdf["hvi_source_year"] = 2023
    heat_gdf["geography_vintage"] = 2020
    heat_gdf["dataset_geography"] = "NTA2020"
    heat_gdf["data_mode"] = "official"
    print(f"   ✓ {len(heat_gdf)} official HVI neighborhoods matched directly to 2020 NTA codes")

    print("📡 Fetching NYC Flood Vulnerability Index on native census tracts…")
    flood_response = _fetch(
        "https://data.cityofnewyork.us/resource/mrjc-v9pm.geojson",
        params={"$limit": "3000"},
    )
    flood_gdf = gpd.GeoDataFrame.from_features(
        flood_response.json().get("features", []), crs="EPSG:4326"
    )
    required_flood = {"geoid", "fshri", "ss_cur", "ss_50s", "ss_80s", "tid_20s", "tid_50s", "tid_80s", "geometry"}
    missing_flood = sorted(required_flood - set(flood_gdf.columns))
    if missing_flood:
        raise ValueError(f"Official FVI data are missing fields: {missing_flood}")
    if len(flood_gdf) != 2209 or flood_gdf["geoid"].duplicated().any():
        raise ValueError(f"Official FVI tract coverage is invalid: {len(flood_gdf)} rows")
    score_fields = ["fshri", "ss_cur", "ss_50s", "ss_80s", "tid_20s", "tid_50s", "tid_80s"]
    for field in score_fields:
        flood_gdf[field] = pd.to_numeric(flood_gdf[field], errors="coerce").astype("Int64")
        if not flood_gdf[field].dropna().between(1, 5).all():
            raise ValueError(f"Official FVI field {field} falls outside the published 1–5 range")
    flood_gdf["tract_name"] = flood_gdf["geoid"].map(lambda value: f"Census tract {str(value)[5:9].lstrip('0') or '0'}.{str(value)[9:]}".rstrip(".0"))
    flood_gdf["dataset_geography"] = "CensusTract"
    flood_gdf["data_mode"] = "official"
    flood_gdf["fvi_source_release"] = 2024
    print(f"   ✓ {len(flood_gdf)} official FVI census tracts loaded")
    live_ok = True

    print(f"\n✅ Live data loaded: {len(merged)} NTAs · "
          f"{int(merged['trees_2015'].sum()):,} trees (2015) · "
          f"{int(merged['trees_2005'].sum()):,} trees (2005)")

except Exception as exc:
    import traceback
    print(f"\n⚠  Live data unavailable: {exc}")
    traceback.print_exc()
    raise RuntimeError(
        "Official data build failed; no fallback values will be published."
    ) from exc

# ════════════════════════════════════════════════════════════════
# 2.  PREPARE OFFICIAL GEOMETRIES
# ════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════
# 3.  DERIVED METRICS
# ════════════════════════════════════════════════════════════════

merged["trees_2015"]   = pd.to_numeric(merged.get("trees_2015", merged.get("trees",0)), errors="coerce").fillna(0)
merged["trees_2005"]   = pd.to_numeric(merged.get("trees_2005", 0), errors="coerce").fillna(0)
merged["area_km2"]     = pd.to_numeric(merged["area_km2"], errors="coerce").fillna(1)
merged["density_2015"] = (merged["trees_2015"] / merged["area_km2"]).round(1)
merged["density_2005"] = (merged["trees_2005"] / merged["area_km2"]).round(1)
merged["tree_change"]  = (merged["trees_2015"] - merged["trees_2005"]).astype(int)
merged["pct_change"]   = ((merged["tree_change"] / merged["trees_2005"].replace(0, np.nan)) * 100).round(1)
merged["data_mode"] = merged.get("data_mode", "official")
merged["generated_at"] = datetime.now(timezone.utc).isoformat()
merged["tree_source_year"] = 2015
merged["geography_vintage"] = 2010
merged["dataset_geography"] = "NTA2010"
merged["tree_2005_unassigned_count"] = tree_2005_unassigned_count
merged["tree_2005_mapping_coverage_pct"] = tree_2005_mapping_coverage_pct

# Publish one reusable, inspectable data product rather than only embedding values.
os.makedirs(os.path.dirname(OUTPUT_DATA), exist_ok=True)
export_cols = [
    "nta_code", "nta_name", "boro_name", "trees_2015", "trees_2005",
    "area_km2", "density_2005", "density_2015", "tree_change", "pct_change",
    "data_mode", "generated_at", "tree_source_year", "geography_vintage",
    "dataset_geography", "geometry",
    "tree_2005_unassigned_count", "tree_2005_mapping_coverage_pct",
]
merged[export_cols].to_file(OUTPUT_DATA, driver="GeoJSON")
if heat_gdf is None:
    raise RuntimeError("Official HVI data are required for publication")
heat_export_cols = [
    "nta_code", "nta_name", "boro_name", "hvi_score", "surface_temp_f",
    "greenspace_pct", "households_ac_pct", "hvi_source_year",
    "geography_vintage", "dataset_geography", "data_mode", "geometry",
]
heat_gdf[heat_export_cols].to_file(OUTPUT_HEAT_DATA, driver="GeoJSON")
if flood_gdf is None:
    raise RuntimeError("Official Flood Vulnerability Index data are required for publication")
flood_export_cols = [
    "geoid", "tract_name", "fshri", "ss_cur", "ss_50s", "ss_80s",
    "tid_20s", "tid_50s", "tid_80s", "fvi_source_release",
    "dataset_geography", "data_mode", "geometry",
]
flood_gdf[flood_export_cols].to_file(OUTPUT_FLOOD_DATA, driver="GeoJSON")

# ════════════════════════════════════════════════════════════════
# 4.  CONSOLE REPORT
# ════════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("  BOROUGH SUMMARY (2015)")
print("─" * 65)
bsumm = (merged.groupby("boro_name")
         .agg(Total_Trees=("trees_2015","sum"),
              Avg_Density =("density_2015","mean"),
              NTAs        =("nta_code","count"))
         .round(0).sort_values("Avg_Density", ascending=False))
print(bsumm.to_string())

print("\n" + "─" * 65)
print("  TREE CHANGE 2005→2015  (biggest losers)")
print("─" * 65)
losers = (merged.nsmallest(8,"tree_change")
          [["nta_name","boro_name","trees_2005","trees_2015","tree_change","pct_change"]]
          .reset_index(drop=True))
print(losers.to_string())

# ════════════════════════════════════════════════════════════════
# 5.  FOLIUM MAP
# ════════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("  BUILDING INTERACTIVE FOLIUM MAP …")
print("─" * 65)

# ── Convert to WGS-84 for Folium ────────────────────────────────
gdf_wgs = merged.to_crs("EPSG:4326") if merged.crs else merged

# ── Stepped colour maps with quantile / percentile breakpoints ───────────
def _ensure_breaks(breaks):
    b = list(breaks)
    for i in range(1, len(b)):
        if b[i] <= b[i-1]:
            b[i] = b[i-1] + 1e-6
    return b

# TREE DENSITY: 5-step green (quantile breakpoints)
_density_colors = ["#edf8e9", "#bae4b3", "#74c476", "#31a354", "#006d2c"]
_density_values = pd.concat([
    merged["density_2005"],
    merged["density_2015"],
]).dropna()
_density_q = _ensure_breaks(
    [float(_density_values.quantile(q)) for q in [0, 0.2, 0.4, 0.6, 0.8, 1.0]]
)
DENSITY_CM = StepColormap(
    colors=_density_colors, index=_density_q,
    vmin=_density_q[0], vmax=_density_q[-1],
    caption="Tree Density (trees / km²)",
)

# TREE CHANGE 2005→2015: 5-step diverging, symmetric around 0
_change_colors = ["#d73027", "#f46d43", "#ffffbf", "#74add1", "#313695"]
_change_abs_max = max(
    abs(float(merged["tree_change"].quantile(0.05))),
    abs(float(merged["tree_change"].quantile(0.95))),
)
_change_vmin, _change_vmax = -_change_abs_max, _change_abs_max
_change_breaks = _ensure_breaks([float(x) for x in np.linspace(_change_vmin, _change_vmax, 6)])
CHANGE_CM = StepColormap(
    colors=_change_colors, index=_change_breaks,
    vmin=_change_vmin, vmax=_change_vmax,
    caption="Tree Count Change (2005 → 2015)",
)

# OFFICIAL 2023 HVI: fixed published ranks, 1 (lowest) to 5 (highest)
_hvi_colors = ["#fff7ec", "#fee8c8", "#fdbb84", "#e34a33", "#7f0000"]
HVI_CM = StepColormap(
    colors=_hvi_colors, index=[1, 2, 3, 4, 5, 6],
    vmin=1, vmax=5, caption="NYC DOHMH Heat Vulnerability Index (1–5)",
)
FVI_CM = StepColormap(
    colors=["#eff3ff", "#bdd7e7", "#6baed6", "#3182bd", "#08519c"],
    index=[1, 2, 3, 4, 5, 6], vmin=1, vmax=5,
    caption="NYC Present Storm-Surge Flood Vulnerability Index (1–5)",
)

# ── Print breakpoints ────────────────────────────────────────────────────
print(f"\n  Tree Density breaks: "
      f"{_density_q[1]:.0f} | {_density_q[2]:.0f} | {_density_q[3]:.0f} | {_density_q[4]:.0f} trees/km²")

# ── Map object ───────────────────────────────────────────────────
m = folium.Map(
    location=[40.7128, -74.0060],
    zoom_start=11,
    tiles=None,
    control_scale=True,
)
min_lon, min_lat, max_lon, max_lat = gdf_wgs.total_bounds
m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]], padding=(12, 12))

folium.TileLayer("CartoDB dark_matter",  name="Dark (default)", show=True).add_to(m)
folium.TileLayer("CartoDB positron",     name="Light", show=False).add_to(m)
folium.TileLayer("OpenStreetMap",        name="Street Map", show=False).add_to(m)

# ── GeoJson layer factory ────────────────────────────────────────
def make_layer(value_col, colormap, layer_name, show=False, frame=None):
    fg = folium.FeatureGroup(name=layer_name, show=show)
    layer_frame = gdf_wgs if frame is None else frame

    def style(feat):
        props = feat["properties"]
        val = props.get(value_col)
        if val is None:
            return {"fillColor": "#39433d", "color": "#7b8580",
                    "weight": 0.5, "fillOpacity": 0.45}
        try:    color = colormap(float(val))
        except (TypeError, ValueError): color = "#39433d"
        return {"fillColor": color, "color": "#ffffff",
                "weight": 0.5, "fillOpacity": 0.85}

    def highlight(feat):
        return {"weight": 2.5, "color": "#ffffcc", "fillOpacity": 0.95}

    GeoJson(
        data=layer_frame.__geo_interface__,
        style_function=style,
        highlight_function=highlight,
    ).add_to(fg)
    return fg

# ── Add all layers ───────────────────────────────────────────────
tree_density_2015_layer = make_layer("density_2015", DENSITY_CM, "Tree Density (2015)", show=True)
tree_density_2005_layer = make_layer("density_2005", DENSITY_CM, "Tree Density (2005)", show=False)
tree_change_layer = make_layer("tree_change", CHANGE_CM, "Tree Change 2005→2015", show=False)
heat_hvi_layer = make_layer(
    "hvi_score", HVI_CM, "Heat Vulnerability Index (2023)",
    show=False, frame=heat_gdf.to_crs("EPSG:4326"),
)
flood_fvi_layer = make_layer(
    "ss_cur", FVI_CM, "Flood Vulnerability - Present Storm Surge",
    show=False, frame=flood_gdf.to_crs("EPSG:4326"),
)

for atlas_layer in (tree_density_2015_layer, tree_density_2005_layer, tree_change_layer, heat_hvi_layer, flood_fvi_layer):
    atlas_layer.add_to(m)

_atlas_layer_vars = {
    "Tree Density (2015)": tree_density_2015_layer.get_name(),
    "Tree Density (2005)": tree_density_2005_layer.get_name(),
    "Tree Change 2005→2015": tree_change_layer.get_name(),
    "Heat Vulnerability Index (2023)": heat_hvi_layer.get_name(),
    "Flood Vulnerability - Present Storm Surge": flood_fvi_layer.get_name(),
}

# ── Tree density heatmap (centroid-based) ────────────────────────
heat_fg = folium.FeatureGroup(name="Tree Density Heatmap", show=False)
heat_pts = []
for _, row in merged.iterrows():
    try:
        lat_ = float(row["lat"])
        lon_ = float(row["lon"])
        weight = min(float(row["density_2015"]) / 1500, 1.0)
        heat_pts.append([lat_, lon_, weight])
    except Exception:
        continue
HeatMap(heat_pts, min_opacity=0.3, radius=25, blur=20,
        gradient={"0.3":"#052e16","0.6":"#15803d","0.85":"#86efac","1.0":"#ffffff"}
        ).add_to(heat_fg)
heat_fg.add_to(m)
_atlas_layer_vars["Tree Density Heatmap"] = heat_fg.get_name()

# ── Layer control ────────────────────────────────────────────────
LayerControl(collapsed=True, position="topright").add_to(m)

# ── Custom legend panel + universal tooltip (injected HTML) ─────
_TOOLTIP_JS = """
(function(){
  function buildTooltipHTML(p){
    var name=window.__activeLayerName||'';
    var displayName=p.nta_name||p.tract_name||'';
    var html='<div style="font-family:DM Sans,sans-serif;min-width:155px">'
      +'<b style="font-size:13px;color:#e8f0e8;display:block;margin-bottom:5px">'
      +displayName+'</b>';
    if(name.indexOf('Tree Density')>=0){
      var treeYear=name.indexOf('(2005)')>=0?'2005':'2015';
      var densityField=treeYear==='2005'?'density_2005':'density_2015';
      var dens=Math.round(parseFloat(p[densityField])||0).toLocaleString();
      html+='<div style="color:#b0cbb0;font-size:11px;margin-bottom:4px">'+dens+' street trees/km² ('+treeYear+')</div>'
           +'<span style="color:#7f9582;font-size:10px">Native 2010 NTA geography</span>';
    }else if(name.indexOf('Heat Vulnerability')>=0){
      var hvi=parseInt(p.hvi_score);
      html+='<div style="color:#fdbb84;font-size:11px;margin-bottom:4px">Official HVI score: '+hvi+' of 5</div>'
           +'<span style="color:#9aa59f;font-size:10px">2023 index · 2020 NTA geography</span>';
    }else if(name.indexOf('Flood Vulnerability')>=0){
      var fvi=p.ss_cur;
      html+='<div style="color:#6baed6;font-size:11px;margin-bottom:4px">Present storm-surge FVI: '+(fvi==null?'Not published':fvi+' of 5')+'</div>'
           +'<span style="color:#9aa59f;font-size:10px">Official NYC census-tract geography</span>';
    }else if(name.indexOf('Change')>=0){
      var chg=parseInt(p.tree_change)||0;
      var cc=chg>=0?'#2fa05e':'#d94f00';
      html+='<div style="color:'+cc+';font-size:11px">'
           +(chg>=0?'+':'-')
           +Math.abs(chg).toLocaleString()+' trees since 2005</div>';
    }else{
      html+='<span style="color:#9aa59f;font-size:10px">Official source geography</span>';
    }
    return html+'</div>';
  }

  // Start with the default-visible layer name
  window.__activeLayerName = 'Tree Density (2015)';
  var tip = document.getElementById('custom-tooltip');

  // Attach mouseover / mousemove / mouseout / click to every GeoJSON feature
  var _attached = {};
  function attachEvents(layer){
    if(!layer||!layer.eachLayer) return;
    layer.eachLayer(function(sub){
      if(sub.feature&&sub.feature.properties){
        var lid = L.stamp(sub);
        if(!_attached[lid]){
          _attached[lid] = true;
          sub.on('mouseover', function(e){
            tip.innerHTML = buildTooltipHTML(e.target.feature.properties);
            tip.style.display = 'block';
          });
          sub.on('mousemove', function(e){
            tip.style.left = (e.originalEvent.clientX + 15) + 'px';
            tip.style.top  = (e.originalEvent.clientY - 10) + 'px';
          });
          sub.on('mouseout', function(){
            tip.style.display = 'none';
          });
          sub.on('click', function(e){
            window.parent.postMessage(
              {type:'nta_click', props:e.target.feature.properties,
               lat:e.latlng&&e.latlng.lat, lng:e.latlng&&e.latlng.lng}, '*');
          });
        }
      }
      attachEvents(sub);
    });
  }

  // Update active layer name when parent dashboard switches layers
  window.addEventListener('message', function(msg){
    if(!msg||!msg.data) return;
    if(msg.data.type==='toggle_layer'&&msg.data.show)
      window.__activeLayerName = msg.data.name;
  });

  // Poll until Leaflet map is ready
  var t = setInterval(function(){
    for(var k in window){
      try{
        var v = window[k];
        if(v&&typeof v==='object'&&v.getZoom&&v.eachLayer){
          clearInterval(t);
          // Attach to all layers already on the map
          v.eachLayer(function(l){ if(l.eachLayer) attachEvents(l); });
          // Also update active layer name when user manually checks LayerControl
          v.on('overlayadd', function(e){
            window.__activeLayerName = e.name;
            attachEvents(e.layer);
            if(window.__legendUpdate) window.__legendUpdate(e.name);
          });
          return;
        }
      }catch(e){}
    }
  }, 200);
})();
"""

# ── Legend HTML (built from computed breakpoints) ────────────────────────
def _lr(bg, lbl):
    return (f"<div class='er'><div class='dt' style='background:{bg}'></div>"
            f"<span>{lbl}</span></div>")

_leg_density = (
    "<h4>Tree Density (trees/km&#xB2;)</h4>"
    + _lr("#edf8e9", f"&lt; {_density_q[1]:.0f}")
    + _lr("#bae4b3", f"{_density_q[1]:.0f} &#x2013; {_density_q[2]:.0f}")
    + _lr("#74c476", f"{_density_q[2]:.0f} &#x2013; {_density_q[3]:.0f}")
    + _lr("#31a354", f"{_density_q[3]:.0f} &#x2013; {_density_q[4]:.0f}")
    + _lr("#006d2c", f"&gt; {_density_q[4]:.0f} trees/km&#xB2;")
)
_leg_change = (
    "<h4>Tree Change 2005&#x2192;2015</h4>"
    + _lr("#d73027", f"{_change_breaks[0]:,.0f} &#x2013; {_change_breaks[1]:,.0f} big loss")
    + _lr("#f46d43", f"{_change_breaks[1]:,.0f} &#x2013; {_change_breaks[2]:,.0f}")
    + _lr("#ffffbf", f"{_change_breaks[2]:,.0f} &#x2013; {_change_breaks[3]:,.0f} no change")
    + _lr("#74add1", f"{_change_breaks[3]:,.0f} &#x2013; {_change_breaks[4]:,.0f}")
    + _lr("#313695", f"{_change_breaks[4]:,.0f} &#x2013; {_change_breaks[5]:,.0f} big gain")
)
_leg_heat = (
    "<h4>Official HVI (2023)</h4>"
    + _lr("#fff7ec", "1 · lowest vulnerability")
    + _lr("#fee8c8", "2")
    + _lr("#fdbb84", "3")
    + _lr("#e34a33", "4")
    + _lr("#7f0000", "5 · highest vulnerability")
    + "<span>Native 2020 NTA boundaries</span>"
)
_leg_flood = (
    "<h4>Present Storm-Surge FVI</h4>"
    + _lr("#eff3ff", "1 · lowest published vulnerability")
    + _lr("#bdd7e7", "2") + _lr("#6baed6", "3")
    + _lr("#3182bd", "4") + _lr("#08519c", "5 · highest published vulnerability")
    + _lr("#39433d", "No published scenario score")
    + "<span>Official NYC census tracts</span>"
)
_legend_js = (
    "function updateLegend(n){"
    "['leg-density','leg-change','leg-heat','leg-flood']"
    ".forEach(function(id){var e=document.getElementById(id);if(e)e.style.display='none';});"
    "var s='leg-density';"
    "if(n.indexOf('Change')>=0)s='leg-change';"
    "else if(n.indexOf('Heat Vulnerability')>=0)s='leg-heat';"
    "else if(n.indexOf('Flood Vulnerability')>=0)s='leg-flood';"
    "var el=document.getElementById(s);if(el)el.style.display='block';}"
    "window.__legendUpdate=updateLegend;"
    "window.addEventListener('message',function(msg){"
    "if(msg&&msg.data&&msg.data.type==='toggle_layer'&&msg.data.show)"
    "updateLegend(msg.data.name);});"
    "setTimeout(function(){updateLegend('Tree Density');},200);"
)

title_html = (
    "<style>"
    "@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@500&family=DM+Sans:wght@400;600&display=swap');"
    ".leaflet-bar,.leaflet-control-layers{border:1px solid rgba(78,203,128,.28)!important;"
    "border-radius:8px!important;overflow:hidden;box-shadow:0 8px 24px rgba(0,0,0,.38)!important}"
    ".leaflet-bar a{background:#0d1117!important;color:#dce9df!important;border-bottom-color:#1a2620!important}"
    ".leaflet-bar a:hover{background:#15201a!important;color:#4ecb80!important}"
    ".leaflet-control-layers{background:#0d1117!important;color:#cce0cc!important;font-family:'DM Sans',sans-serif}"
    ".leaflet-control-layers-toggle{background-color:#0d1117!important;filter:invert(1) opacity(.72)}"
    ".leaflet-control-layers-expanded{padding:10px 12px!important}"
    ".leaflet-control-layers-separator{border-top-color:#26332b!important}"
    ".leaflet-control-scale-line{background:rgba(13,17,23,.88)!important;color:#cce0cc!important;"
    "border-color:#4d6b52!important;text-shadow:none!important}"
    ".leaflet-control-attribution{background:rgba(13,17,23,.82)!important;color:#6f8574!important}"
    ".leaflet-control-attribution a{color:#79b98e!important}"
    ".eql{position:fixed;bottom:28px;left:54px;z-index:9999;background:rgba(8,12,8,0.88);"
    "border:1px solid #222;padding:8px 10px;border-radius:4px;box-shadow:0 2px 12px rgba(0,0,0,0.4);"
    "min-width:170px}"
    ".eql h4{margin:0 0 5px;font-size:9px;color:#5a7a5a;text-transform:uppercase;letter-spacing:1px;font-family:'DM Sans',sans-serif}"
    ".eql .er{display:flex;align-items:center;gap:6px;margin:2px 0}"
    ".eql .dt{width:9px;height:9px;border-radius:2px;flex-shrink:0}"
    ".eql span{font-size:10px;color:#b0c8b0;font-family:'DM Sans',sans-serif}"
    "@media(max-width:600px){.eql{left:12px;bottom:28px;transform:scale(.82);transform-origin:bottom left}}"
    "</style>"
    "<div id='custom-tooltip' style='"
    "position:fixed;background:#0d1117;color:#cce0cc;padding:8px 12px;"
    "border-radius:4px;font-family:DM Sans,sans-serif;font-size:12px;"
    "pointer-events:none;z-index:99999;border:1px solid #2fa05e;"
    "display:none;max-width:240px;line-height:1.5;"
    "'></div>"
    "<div class='eql'>"
    "<div id='leg-density'>" + _leg_density + "</div>"
    "<div id='leg-change' style='display:none'>" + _leg_change + "</div>"
    "<div id='leg-heat' style='display:none'>" + _leg_heat + "</div>"
    "<div id='leg-flood' style='display:none'>" + _leg_flood + "</div>"
    "</div>"
    "<script>window.__atlasLayerVars=" + json.dumps(_atlas_layer_vars) + ";</script>"
    "<script>" + _legend_js + "</script>"
    "<script>" + _TOOLTIP_JS + "</script>"
)
m.get_root().html.add_child(Element(title_html))

# ── Save ─────────────────────────────────────────────────────────
m.save(OUTPUT_HTML)
# Folium templates include trailing spaces. Normalize the generated artifact so
# pull-request diffs and whitespace checks stay clean and reproducible.
with open(OUTPUT_HTML, encoding="utf-8") as handle:
    normalized_html = "\n".join(line.rstrip() for line in handle.read().splitlines()) + "\n"
with open(OUTPUT_HTML, "w", encoding="utf-8") as handle:
    handle.write(normalized_html)
print(f"\n✅  Map saved → {OUTPUT_HTML}")
print(f"    Open in any browser for the interactive map.")
