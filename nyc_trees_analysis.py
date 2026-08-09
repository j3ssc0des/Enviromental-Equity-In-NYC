

#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║   NYC STREET TREE CENSUS  ·  Green Space Inequity Analysis       ║
║   Data: NYC Open Data 2005 & 2015 Street Tree Census             ║
║   Tools: Python · Pandas · GeoPandas · Folium                    ║
╚══════════════════════════════════════════════════════════════════╝

HOW TO USE:
  LIVE_DATA = True: build from declared official/public sources (default)
  LIVE_DATA = False: use clearly labelled demo data for interface work only

  Publication builds fail closed when a required source is unavailable.
  Demo values are never allowed into CI or deployment output.

OUTPUT: nyc_trees_map.html  (interactive Folium choropleth map)
"""

import warnings, json, textwrap, io, time, os
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import folium
from folium import GeoJson, LayerControl
from folium.plugins import HeatMap, MiniMap
from branca.colormap import LinearColormap, StepColormap
from branca.element import Element
import geopandas as gpd
from shapely.geometry import Polygon, Point, mapping
warnings.filterwarnings("ignore")

# ────────────────────────────────────────────────────────────────
LIVE_DATA   = True    # Set False to use embedded dataset
OUTPUT_HTML = "nyc_trees_map.html"
OUTPUT_DATA = "data/processed/nta_environmental_snapshot.geojson"
ALLOW_DEMO_DATA = os.getenv("ALLOW_DEMO_DATA", "false").lower() == "true"
# ────────────────────────────────────────────────────────────────

print("=" * 65)
print("  🌳  NYC Green Space Inequity: Street Tree Census Analysis")
print("=" * 65)


# ════════════════════════════════════════════════════════════════
# 1.  DATA
#     Embedded dataset is always defined. It acts as both the
#     offline fallback AND the income lookup for live mode
#     (income is not in the tree census datasets).
# ════════════════════════════════════════════════════════════════

NTA_RECORDS = [
    # code, name, borough, lat, lon, area_km2, trees_15, trees_05, income
    # ── MANHATTAN ──────────────────────────────────────────────────────
    ("MN2501","Battery Park City-Lower Manhattan","Manhattan",40.7127,-74.0148,1.1, 820, 690,140000),
    ("MN2502","Greenwich Village-SoHo",           "Manhattan",40.7264,-74.0026,1.4,1350,1100,125000),
    ("MN2503","Chinatown",                        "Manhattan",40.7158,-73.9970,0.9, 480, 390, 38000),
    ("MN2504","Lower East Side",                  "Manhattan",40.7153,-73.9853,1.8,1120, 940, 32000),
    ("MN2505","Upper East Side-Carnegie Hill",    "Manhattan",40.7749,-73.9565,3.2,3200,2900,145000),
    ("MN2506","Lenox Hill-Roosevelt Island",      "Manhattan",40.7665,-73.9607,2.8,2800,2500,132000),
    ("MN2507","Central Harlem South",             "Manhattan",40.8134,-73.9468,2.2,2100,1750, 36000),
    ("MN2508","East Harlem (El Barrio)",          "Manhattan",40.7957,-73.9376,3.1,2950,2600, 30000),
    ("MN2509","Washington Heights North",         "Manhattan",40.8501,-73.9396,2.7,2700,2200, 38000),
    ("MN2510","Washington Heights South",         "Manhattan",40.8397,-73.9401,2.4,2400,2050, 40000),
    ("MN2511","Inwood",                           "Manhattan",40.8676,-73.9221,2.9,3100,2700, 44000),
    ("MN2701","West Village",                     "Manhattan",40.7341,-74.0038,1.2,1180, 950,155000),
    ("MN2702","Chelsea-Hudson Yards",             "Manhattan",40.7465,-74.0014,2.6,1900,1650,130000),
    ("MN2703","Hell's Kitchen-Clinton",           "Manhattan",40.7625,-73.9912,2.1,1750,1520, 90000),
    ("MN2704","Midtown-Midtown South",            "Manhattan",40.7549,-73.9840,3.5,1420,1280,105000),
    ("MN2705","Murray Hill-Kips Bay",             "Manhattan",40.7465,-73.9771,1.6,1250,1100,115000),
    ("MN2706","Stuyvesant Town-Cooper Village",   "Manhattan",40.7315,-73.9786,0.8, 740, 680,105000),
    ("MN2707","East Village",                     "Manhattan",40.7268,-73.9816,1.7,1100, 960, 72000),
    ("MN2708","Upper West Side",                  "Manhattan",40.7870,-73.9754,3.0,3100,2800,130000),
    ("MN2709","Morningside Heights",              "Manhattan",40.8101,-73.9610,1.9,2000,1800, 55000),
    ("MN2710","Hamilton Heights",                 "Manhattan",40.8231,-73.9522,1.8,1900,1600, 48000),
    # ── BROOKLYN ───────────────────────────────────────────────────────
    ("BK0101","Greenpoint",                       "Brooklyn",40.7292,-73.9519,2.8,3200,2700, 78000),
    ("BK0102","Williamsburg",                     "Brooklyn",40.7081,-73.9571,3.9,3900,3100, 72000),
    ("BK0201","Clinton Hill",                     "Brooklyn",40.6883,-73.9617,1.9,2100,1800, 92000),
    ("BK0202","Fort Greene",                      "Brooklyn",40.6893,-73.9752,1.7,2000,1700, 88000),
    ("BK0203","Brooklyn Heights-Cobble Hill",     "Brooklyn",40.6956,-73.9937,2.1,2300,2000,145000),
    ("BK0204","Carroll Gardens-Red Hook",         "Brooklyn",40.6773,-73.9987,3.8,4200,3600, 82000),
    ("BK0301","Crown Heights North",              "Brooklyn",40.6737,-73.9373,4.1,4800,4100, 48000),
    ("BK0302","Crown Heights South",              "Brooklyn",40.6571,-73.9373,3.8,4200,3500, 42000),
    ("BK0401","East New York",                    "Brooklyn",40.6501,-73.8826,9.2,7200,5800, 32000),
    ("BK0402","Cypress Hills-City Line",          "Brooklyn",40.6727,-73.8847,4.2,3900,3100, 34000),
    ("BK0501","Flatbush",                         "Brooklyn",40.6419,-73.9580,5.1,5600,4800, 52000),
    ("BK0502","East Flatbush-Farragut",           "Brooklyn",40.6376,-73.9393,5.8,6200,5200, 46000),
    ("BK0601","Canarsie",                         "Brooklyn",40.6337,-73.9029,7.4,7800,6500, 58000),
    ("BK0701","Bay Ridge",                        "Brooklyn",40.6313,-74.0300,6.9,7500,6600, 72000),
    ("BK0702","Dyker Heights",                    "Brooklyn",40.6246,-74.0113,3.4,4100,3500, 78000),
    ("BK0801","Bensonhurst West",                 "Brooklyn",40.6108,-73.9978,4.6,5200,4400, 62000),
    ("BK0802","Bensonhurst East",                 "Brooklyn",40.6092,-73.9835,4.3,4800,4100, 58000),
    ("BK0901","Sunset Park West",                 "Brooklyn",40.6497,-74.0027,3.6,3800,3100, 48000),
    ("BK1001","Borough Park",                     "Brooklyn",40.6275,-73.9960,4.8,5300,4500, 56000),
    ("BK1101","Sheepshead Bay",                   "Brooklyn",40.5990,-73.9464,7.2,8100,6800, 68000),
    ("BK1201","Brownsville",                      "Brooklyn",40.6637,-73.9113,4.7,3900,3000, 26000),
    ("BK1202","Ocean Hill",                       "Brooklyn",40.6784,-73.9156,2.3,2400,1900, 30000),
    ("BK1301","Flatlands",                        "Brooklyn",40.6198,-73.9327,8.1,9200,7800, 64000),
    ("BK1401","Park Slope-Gowanus",               "Brooklyn",40.6723,-73.9844,4.2,4900,4200,115000),
    ("BK1501","Prospect Heights",                 "Brooklyn",40.6769,-73.9670,1.8,2100,1800, 98000),
    # ── BRONX ──────────────────────────────────────────────────────────
    ("BX0101","Wakefield-Woodlawn",               "Bronx",40.8988,-73.8593,7.3,6800,5800, 52000),
    ("BX0201","Norwood",                          "Bronx",40.8804,-73.8764,3.8,3600,3000, 46000),
    ("BX0301","Fordham South",                    "Bronx",40.8596,-73.8978,2.9,2700,2200, 34000),
    ("BX0302","Fordham North",                    "Bronx",40.8698,-73.8881,3.2,3000,2500, 36000),
    ("BX0401","Mott Haven-Port Morris",           "Bronx",40.8088,-73.9217,3.6,2400,1900, 24000),
    ("BX0402","Melrose South-Mott Haven North",   "Bronx",40.8201,-73.9216,2.8,1900,1500, 26000),
    ("BX0501","Highbridge",                       "Bronx",40.8372,-73.9249,2.4,2300,1800, 28000),
    ("BX0601","Hunts Point",                      "Bronx",40.8121,-73.8944,4.8,2900,2300, 22000),
    ("BX0701","Longwood",                         "Bronx",40.8237,-73.9003,2.1,2000,1600, 25000),
    ("BX0801","Morrisania-Melrose",               "Bronx",40.8330,-73.9092,3.2,2800,2200, 28000),
    ("BX0901","Soundview-Bruckner",               "Bronx",40.8213,-73.8722,5.7,5100,4200, 36000),
    ("BX1001","Pelham Parkway",                   "Bronx",40.8603,-73.8661,5.2,5600,4700, 54000),
    ("BX1101","Parkchester",                      "Bronx",40.8422,-73.8641,4.6,4200,3500, 44000),
    ("BX1201","Throgs Neck-Co-op City",           "Bronx",40.8382,-73.8310,12.4,9800,7800, 58000),
    ("BX1301","Riverdale-Spuyten Duyvil",         "Bronx",40.9011,-73.9102,6.8,7800,6500, 90000),
    ("BX1401","Country Club",                     "Bronx",40.8399,-73.8301,5.1,5400,4500, 62000),
    # ── QUEENS ─────────────────────────────────────────────────────────
    ("QN0101","Astoria",                          "Queens",40.7721,-73.9303,5.7,5800,4900, 68000),
    ("QN0102","Woodside",                         "Queens",40.7448,-73.9014,4.2,4500,3800, 64000),
    ("QN0201","Flushing",                         "Queens",40.7675,-73.8330,7.8,7500,6200, 58000),
    ("QN0202","Murray Hill-Flushing",             "Queens",40.7563,-73.8256,5.4,5600,4700, 62000),
    ("QN0301","Jamaica",                          "Queens",40.7068,-73.8038,8.3,7200,5900, 46000),
    ("QN0302","South Jamaica",                    "Queens",40.6896,-73.7921,5.1,4300,3500, 38000),
    ("QN0401","Richmond Hill",                    "Queens",40.6995,-73.8334,5.8,5900,4900, 60000),
    ("QN0402","Woodhaven",                        "Queens",40.6960,-73.8562,4.5,5200,4400, 62000),
    ("QN0501","Forest Hills-Rego Park",           "Queens",40.7189,-73.8501,7.1,8200,6900, 88000),
    ("QN0502","Kew Gardens",                      "Queens",40.7079,-73.8295,3.8,4600,3900, 82000),
    ("QN0601","Far Rockaway-Bayswater",           "Queens",40.6052,-73.7562,9.2,6500,5200, 42000),
    ("QN0701","Howard Beach-Lindenwood",          "Queens",40.6596,-73.8476,8.9,9100,7600, 72000),
    ("QN0801","Maspeth",                          "Queens",40.7296,-73.9097,5.6,6200,5200, 76000),
    ("QN0901","Fresh Meadows-Utopia",             "Queens",40.7310,-73.7891,9.8,11200,9400, 90000),
    ("QN1001","Bayside-Bayside Hills",            "Queens",40.7663,-73.7726,8.4,10200,8700, 95000),
    ("QN1101","Springfield Gardens North",        "Queens",40.6666,-73.7686,6.7,6400,5200, 52000),
    ("QN1201","Jackson Heights",                  "Queens",40.7516,-73.8830,3.9,4200,3500, 55000),
    ("QN1301","Long Island City-Astoria",         "Queens",40.7447,-73.9483,4.4,4100,3300, 76000),
    # ── STATEN ISLAND ──────────────────────────────────────────────────
    ("SI0101","St. George-New Brighton",          "Staten Island",40.6439,-74.0901,5.6,6200,5100, 64000),
    ("SI0201","Mariner's Harbor-Arlington",       "Staten Island",40.6343,-74.1564,7.8,8400,7000, 58000),
    ("SI0301","West Brighton-Port Richmond",      "Staten Island",40.6346,-74.1322,6.4,7100,5900, 60000),
    ("SI0401","Stapleton-Rosebank",               "Staten Island",40.6248,-74.0739,5.1,5700,4700, 62000),
    ("SI0501","Richmond Town-Richmond Valley",    "Staten Island",40.5698,-74.1554,14.2,18400,14500, 82000),
    ("SI0601","Great Kills",                      "Staten Island",40.5533,-74.1500,9.7,12300,10100, 86000),
    ("SI0701","Tottenville-Charleston",           "Staten Island",40.5119,-74.2004,21.8,28200,22000, 88000),
    ("SI0801","Annadale-Huguenot",                "Staten Island",40.5368,-74.1682,12.1,15600,12400, 90000),
    ("SI0901","New Springville-Bloomfield",       "Staten Island",40.5859,-74.1726,11.4,14200,11200, 84000),
    ("SI1001","South Shore",                      "Staten Island",40.5348,-74.1907,10.8,13500,10700, 87000),
]

_COLS = ["nta_code","nta_name","boro_name","lat","lon","area_km2",
         "trees_2015","trees_2005","median_income"]

# Embedded values are demo-only and are never mixed into a live build.

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

def _fetch_acs_income():
    """Load the latest audited ACS five-year tract-income payload."""
    rows = []
    cache_path="data/raw/acs_income.json"
    if os.path.exists(cache_path):
        with open(cache_path,encoding="utf-8") as handle:
            payload=json.load(handle)
        print("   ✓ Using ACS payload verified by source audit")
    else:
        response = _fetch(
            "https://api.censusreporter.org/1.0/data/show/latest",
            params={"table_ids":"B19013,B11001", "geo_ids":"140|04000US36"},
            timeout=90,
        )
        payload=response.json()
    release_year=int(str(payload["release"]["years"]).split("-")[-1])
    nyc_counties={"005","047","061","081","085"}
    for geoid,tables in payload["data"].items():
        raw=geoid.replace("14000US","")
        if raw[2:5] not in nyc_counties:
            continue
        rows.append({"COUNTY":raw[2:5],"TRACT":raw[5:11],
            "tract_income":tables["B19013"]["estimate"].get("B19013001"),
            "tract_income_moe":tables["B19013"]["error"].get("B19013001"),
            "households":tables["B11001"]["estimate"].get("B11001001"),
            "income_source_year":release_year})
    acs = pd.DataFrame(rows)
    for col in ("tract_income", "tract_income_moe", "households"):
        acs[col] = pd.to_numeric(acs[col], errors="coerce")
    acs.loc[acs["tract_income"] < 0, "tract_income"] = np.nan
    acs.loc[acs["households"] <= 0, "households"] = np.nan
    acs["COUNTY"] = acs["COUNTY"].astype(str).str.zfill(3)
    acs["TRACT"] = acs["TRACT"].astype(str).str.zfill(6)
    return acs

def _aggregate_income_to_nta(acs, crosswalk):
    """Approximate NTA median from tract medians, weighted by households."""
    joined = crosswalk[["COUNTY", "TRACT", "nta_code"]].drop_duplicates().merge(
        acs, on=["COUNTY", "TRACT"], how="left"
    )
    summaries=[]
    for nta_code,group in joined.dropna(subset=["nta_code"]).groupby("nta_code"):
        valid = group.dropna(subset=["tract_income", "households"])
        total_households = group["households"].sum(min_count=1)
        covered_households = valid["households"].sum(min_count=1)
        if valid.empty or not covered_households:
            summaries.append({"nta_code":nta_code,"median_income":np.nan,
                "income_coverage_pct":0.0,"residential_households":total_households})
            continue
        summaries.append({"nta_code":nta_code,
            "median_income":np.average(valid["tract_income"],weights=valid["households"]),
            "income_coverage_pct":100*covered_households/total_households if total_households else 0.0,
            "residential_households":total_households})
    result=pd.DataFrame(summaries)
    result["median_income"] = result["median_income"].round()
    result["income_coverage_pct"] = result["income_coverage_pct"].round(1)
    return result

def _assert_unique_nta(frame, stage):
    duplicates=frame.loc[frame["nta_code"].duplicated(keep=False),"nta_code"].dropna().unique()
    if len(duplicates):
        raise ValueError(f"Duplicate NTA codes after {stage}: {sorted(duplicates.tolist())}")

# ── Live fetch ────────────────────────────────────────────────────────────
live_ok = False
tree_2005_unassigned_count = 0
tree_2005_mapping_coverage_pct = 100.0

if LIVE_DATA:
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

        print("📡 Building current-tract to 2010-NTA spatial crosswalk…")
        current_tracts=gpd.read_file(
            "https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_36_tract_500k.zip"
        )
        current_tracts=current_tracts[current_tracts["COUNTYFP"].isin(nyc_counties)].copy()
        current_tracts["COUNTY"]=current_tracts["COUNTYFP"].astype(str).str.zfill(3)
        current_tracts["TRACT"]=current_tracts["TRACTCE"].astype(str).str.zfill(6)
        tract_points=current_tracts.to_crs("EPSG:2263")
        tract_points["geometry"]=tract_points.geometry.representative_point()
        nta_shapes=gdf_boundaries[["nta_code","geometry"]].to_crs("EPSG:2263")
        current_xwalk=gpd.sjoin(
            tract_points[["COUNTY","TRACT","geometry"]], nta_shapes,
            how="left", predicate="within",
        )[["COUNTY","TRACT","nta_code"]]

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

        print("📡 Fetching current ACS five-year household income…")
        acs_income=_fetch_acs_income()
        income_by_nta = _aggregate_income_to_nta(acs_income, current_xwalk)
        merged = merged.merge(income_by_nta, on="nta_code", how="left")
        _assert_unique_nta(merged,"income join")
        merged["income_estimated"] = True
        merged["income_source_year"] = int(acs_income["income_source_year"].max())
        merged["income_source"] = "ACS five-year B19013 via Census Reporter; household-weighted tract approximation"

        # Centroid lat/lon for circle markers
        cents = merged.to_crs("EPSG:2263").geometry.centroid.to_crs("EPSG:4326")
        merged["lat"] = cents.y.round(4)
        merged["lon"] = cents.x.round(4)

        merged = gpd.GeoDataFrame(merged, geometry="geometry", crs="EPSG:4326")
        live_ok = True

        print(f"\n✅ Live data loaded: {len(merged)} NTAs · "
              f"{int(merged['trees_2015'].sum()):,} trees (2015) · "
              f"{int(merged['trees_2005'].sum()):,} trees (2005)")

    except Exception as exc:
        import traceback
        print(f"\n⚠  Live data unavailable: {exc}")
        traceback.print_exc()
        if not ALLOW_DEMO_DATA:
            raise RuntimeError(
                "Official data build failed. Refusing to publish demo values; "
                "set ALLOW_DEMO_DATA=true only for local interface development."
            ) from exc
        print("   Falling back to clearly labelled demo dataset…")

# ── Embedded fallback ─────────────────────────────────────────────────────
if not live_ok:
    if not LIVE_DATA:
        print("\n📦 Using embedded census dataset (set LIVE_DATA=True for real API)")

    df_data = pd.DataFrame(NTA_RECORDS, columns=_COLS)
    df_data["income_coverage_pct"] = 0.0
    df_data["income_estimated"] = True
    df_data["income_source"] = "DEMO DATA: not for publication"
    df_data["residential_households"] = np.nan
    df_data["data_mode"] = "demo"
    print(f"   ✓  {df_data['trees_2015'].sum():,} trees  ·  {len(df_data)} NTAs  (embedded)")


# ════════════════════════════════════════════════════════════════
# 2.  PREPARE GEOMETRIES
#     Live mode  → real NTA polygons from the API (already in `merged`)
#     Embedded   → approximate hexagons generated from centroid + area
# ════════════════════════════════════════════════════════════════

def hex_polygon(lat, lon, area_km2):
    """Return a hexagonal Shapely polygon approximating the NTA area."""
    r_lat = (area_km2 / (1.5 * np.sqrt(3))) ** 0.5 / 111.0
    r_lon = r_lat / np.cos(np.radians(lat))
    angles = np.linspace(0, 2 * np.pi, 7)[:-1]
    pts = [(lon + r_lon * np.sin(a), lat + r_lat * np.cos(a)) for a in angles]
    return Polygon(pts)


if not live_ok:
    df_data["geometry"] = df_data.apply(
        lambda r: hex_polygon(r.lat, r.lon, r.area_km2), axis=1
    )
    merged = gpd.GeoDataFrame(df_data, geometry="geometry", crs="EPSG:4326")


# PM2.5 is catalogued but not transformed to NTA geography. It remains null
# until a documented spatial or population-weighted crosswalk is implemented.
merged["pm25"] = np.nan
merged["pm25_estimated"] = False


# ════════════════════════════════════════════════════════════════
# 3.  DERIVED METRICS
# ════════════════════════════════════════════════════════════════

merged["trees_2015"]   = pd.to_numeric(merged.get("trees_2015", merged.get("trees",0)), errors="coerce").fillna(0)
merged["trees_2005"]   = pd.to_numeric(merged.get("trees_2005", 0), errors="coerce").fillna(0)
merged["area_km2"]     = pd.to_numeric(merged["area_km2"], errors="coerce").fillna(1)
merged["median_income"]= pd.to_numeric(merged["median_income"], errors="coerce")

merged["density_2015"] = (merged["trees_2015"] / merged["area_km2"]).round(1)
merged["density_2005"] = (merged["trees_2005"] / merged["area_km2"]).round(1)
merged["tree_change"]  = (merged["trees_2015"] - merged["trees_2005"]).astype(int)
merged["pct_change"]   = ((merged["tree_change"] / merged["trees_2005"].replace(0, np.nan)) * 100).round(1)
merged["data_mode"] = merged.get("data_mode", "official")
merged["generated_at"] = datetime.now(timezone.utc).isoformat()
merged["tree_source_year"] = 2015
merged["tree_2005_unassigned_count"] = tree_2005_unassigned_count
merged["tree_2005_mapping_coverage_pct"] = tree_2005_mapping_coverage_pct
if "income_source_year" not in merged:
    merged["income_source_year"] = np.nan

# Parks, airports, cemeteries, and other near-zero-household planning areas
# remain visible for context but never compete in community investment rankings.
_nonresidential_name = merged["nta_name"].str.contains(
    r"airport|park-cemetery|cemetery|park$|riker|fort totten|governors island|ellis island|liberty island",
    case=False, regex=True, na=False,
)
_enough_households = pd.to_numeric(
    merged.get("residential_households"), errors="coerce"
).fillna(0) >= 100
_enough_income_coverage = pd.to_numeric(
    merged.get("income_coverage_pct"), errors="coerce"
).fillna(0) >= 90
merged["investment_eligible"] = (
    _enough_households & ~_nonresidential_name & _enough_income_coverage
)
merged["area_context"] = np.select(
    [~_enough_households | _nonresidential_name, ~_enough_income_coverage],
    ["Non-residential/context", "Insufficient income coverage"],
    default="Residential/community",
)

eligible = merged["investment_eligible"]
merged["inc_norm"] = np.nan
merged["den_norm"] = np.nan
merged.loc[eligible, "inc_norm"] = merged.loc[eligible, "median_income"].rank(pct=True)
merged.loc[eligible, "den_norm"] = merged.loc[eligible, "density_2015"].rank(pct=True)
merged["heat_proxy"]  = (1 - merged["den_norm"] * 0.6 - merged["inc_norm"] * 0.4).round(3)
merged["heat_proxy_method"] = "Project proxy: 60% street-tree density percentile + 40% income percentile"

# Project screening score. PM2.5 is excluded until a valid spatial crosswalk exists.
merged["underserved"] = (
    0.55 * (1 - merged["den_norm"]) +
    0.45 * (1 - merged["inc_norm"])
).round(3)
merged.loc[merged[["density_2015", "median_income"]].isna().any(axis=1), "underserved"] = np.nan
merged.loc[~merged["investment_eligible"], ["underserved", "heat_proxy"]] = np.nan
merged["screening_score_method"] = "Project-defined: 55% tree density percentile + 45% income percentile"

# Bucket for labelling
def bucket(val, labels=("Lower Priority","Below Average","Middle","Above Average","Higher Priority")):
    if pd.isna(val):
        return "Insufficient Data"
    breaks = [0, 0.30, 0.50, 0.65, 0.80, 1.01]
    for i in range(len(breaks)-1):
        if breaks[i] <= val < breaks[i+1]:
            return labels[i]
    return labels[-1]

merged["equity_label"] = merged["underserved"].apply(bucket)

# Publish one reusable, inspectable data product rather than only embedding values.
os.makedirs(os.path.dirname(OUTPUT_DATA), exist_ok=True)
export_cols = [
    "nta_code", "nta_name", "boro_name", "trees_2015", "trees_2005",
    "area_km2", "density_2015", "tree_change", "pct_change",
    "median_income", "income_coverage_pct", "income_estimated", "income_source",
    "residential_households", "investment_eligible", "area_context",
    "heat_proxy", "heat_proxy_method", "underserved", "screening_score_method",
    "equity_label", "pm25", "pm25_estimated", "data_mode", "generated_at",
    "tree_source_year", "income_source_year", "geometry",
    "tree_2005_unassigned_count", "tree_2005_mapping_coverage_pct",
]
merged[export_cols].to_file(OUTPUT_DATA, driver="GeoJSON")

# ════════════════════════════════════════════════════════════════
# 4.  CONSOLE REPORT
# ════════════════════════════════════════════════════════════════

print("\n" + "─" * 65)
print("  BOROUGH SUMMARY (2015)")
print("─" * 65)
bsumm = (merged.groupby("boro_name")
         .agg(Total_Trees=("trees_2015","sum"),
              Avg_Density =("density_2015","mean"),
              Avg_Income  =("median_income","mean"),
              NTAs        =("nta_code","count"))
         .round(0).sort_values("Avg_Density", ascending=False))
print(bsumm.to_string())

print("\n" + "─" * 65)
print("  TOP 10 PROJECT SCREENING SCORES")
print("─" * 65)
top10 = (merged[merged["investment_eligible"]].nlargest(10, "underserved")
         [["nta_name","boro_name","density_2015","median_income","underserved","equity_label"]]
         .reset_index(drop=True))
top10.index += 1
print(top10.to_string())

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
_density_q = _ensure_breaks(
    [float(merged["density_2015"].quantile(q)) for q in [0, 0.2, 0.4, 0.6, 0.8, 1.0]]
)
DENSITY_CM = StepColormap(
    colors=_density_colors, index=_density_q,
    vmin=_density_q[0], vmax=_density_q[-1],
    caption="Tree Density (trees / km²)",
)

# MEDIAN INCOME: 5-step purple (20th/40th/60th/80th percentile breaks)
_income_colors = ["#f2f0f7", "#cbc9e2", "#9e9ac8", "#756bb1", "#54278f"]
_income_q = _ensure_breaks(
    [float(merged["median_income"].quantile(q)) for q in [0, 0.2, 0.4, 0.6, 0.8, 1.0]]
)
INCOME_CM = StepColormap(
    colors=_income_colors, index=_income_q,
    vmin=_income_q[0], vmax=_income_q[-1],
    caption="Median Household Income ($)",
)

# PROJECT SCREENING SCORE: 5-step yellow-to-dark-red (quantile breaks)
_underserved_colors = ["#ffffcc", "#fed976", "#fd8d3c", "#e31a1c", "#800026"]
_underserved_q = _ensure_breaks(
    [float(merged["underserved"].quantile(q)) for q in [0, 0.2, 0.4, 0.6, 0.8, 1.0]]
)
UNDERSERVED_CM = StepColormap(
    colors=_underserved_colors, index=_underserved_q,
    vmin=_underserved_q[0], vmax=_underserved_q[-1],
    caption="Project Screening Score (lower to higher)",
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

# TREE-AND-INCOME PROXY: 5-step fire scale (quantile breaks)
_heat_colors = ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"]
_heat_q = _ensure_breaks(
    [float(merged["heat_proxy"].quantile(q)) for q in [0, 0.2, 0.4, 0.6, 0.8, 1.0]]
)
HEAT_CM = StepColormap(
    colors=_heat_colors, index=_heat_q,
    vmin=_heat_q[0], vmax=_heat_q[-1],
    caption="Tree + Income Screening Proxy",
)

# ── Print breakpoints ────────────────────────────────────────────────────
print(f"\n  Tree Density breaks: "
      f"{_density_q[1]:.0f} | {_density_q[2]:.0f} | {_density_q[3]:.0f} | {_density_q[4]:.0f} trees/km²")
print(f"  Income breaks: "
      f"${_income_q[1]:,.0f} | ${_income_q[2]:,.0f} | ${_income_q[3]:,.0f} | ${_income_q[4]:,.0f}")
print(f"  Screening score breaks: "
      f"{_underserved_q[1]:.3f} | {_underserved_q[2]:.3f} | {_underserved_q[3]:.3f} | {_underserved_q[4]:.3f}")
print(f"  Tree + income proxy breaks: "
      f"{_heat_q[1]:.3f} | {_heat_q[2]:.3f} | {_heat_q[3]:.3f} | {_heat_q[4]:.3f}")

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
EQUITY_COLORS = {
    "Lower Priority":  "#2fa05e",
    "Below Average":   "#a8e6bf",
    "Middle":          "#f5b800",
    "Above Average":   "#d94f00",
    "Higher Priority": "#6d0000",
    "Insufficient Data":"#64706a",
}

def make_layer(value_col, colormap, layer_name, show=False):
    fg = folium.FeatureGroup(name=layer_name, show=show)

    def style(feat):
        props = feat["properties"]
        val = props.get(value_col)
        if val is None or (value_col in {"underserved", "heat_proxy"} and not props.get("investment_eligible")):
            return {"fillColor": "#39433d", "color": "#7b8580",
                    "weight": 0.5, "fillOpacity": 0.45}
        try:    color = colormap(float(val))
        except (TypeError, ValueError): color = "#39433d"
        return {"fillColor": color, "color": "#ffffff",
                "weight": 0.5, "fillOpacity": 0.85}

    def highlight(feat):
        return {"weight": 2.5, "color": "#ffffcc", "fillOpacity": 0.95}

    GeoJson(
        data=gdf_wgs.__geo_interface__,
        style_function=style,
        highlight_function=highlight,
    ).add_to(fg)
    return fg

# ── Add all layers ───────────────────────────────────────────────
tree_density_layer = make_layer("density_2015", DENSITY_CM, "Tree Density (2015)", show=True)
income_layer = make_layer("median_income", INCOME_CM, "Median Household Income", show=False)
screening_layer = make_layer("underserved", UNDERSERVED_CM, "Project Screening Score", show=False)
tree_change_layer = make_layer("tree_change", CHANGE_CM, "Tree Change 2005→2015", show=False)
proxy_layer = make_layer("heat_proxy", HEAT_CM, "Tree + Income Screening Proxy", show=False)

for atlas_layer in (tree_density_layer, income_layer, screening_layer, tree_change_layer, proxy_layer):
    atlas_layer.add_to(m)

_atlas_layer_vars = {
    "Tree Density (2015)": tree_density_layer.get_name(),
    "Median Household Income": income_layer.get_name(),
    "Project Screening Score": screening_layer.get_name(),
    "Tree Change 2005→2015": tree_change_layer.get_name(),
    "Tree + Income Screening Proxy": proxy_layer.get_name(),
}

# ── Higher-score screening markers ───────────────────────────────
priority_fg = folium.FeatureGroup(name="Higher-score areas (top 15)", show=False)
top15 = merged[merged["investment_eligible"]].nlargest(15, "underserved")
for _, row in top15.iterrows():
    try:
        lat_, lon_ = float(row["lat"]), float(row["lon"])
    except Exception:
        continue

    folium.CircleMarker(
        location=[lat_, lon_],
        radius=8,
        color="#ff3300",
        weight=2,
        fill=True,
        fill_color="#ff6600",
        fill_opacity=0.85,
        tooltip=f"{row['nta_name']} ({row['boro_name']})\n"
                f"Screening score: {row['underserved']:.2f}  |  "
                f"Density: {row['density_2015']:.0f} trees/km²  |  "
                f"Income: ${int(row['median_income']):,}",
    ).add_to(priority_fg)
priority_fg.add_to(m)

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

# ── Layer control ────────────────────────────────────────────────
LayerControl(collapsed=True, position="topright").add_to(m)

# ── Custom legend panel + universal tooltip (injected HTML) ─────
_TOOLTIP_JS = """
(function(){
  var EQ={'Lower Priority':'#2fa05e','Below Average':'#a8e6bf',
          'Middle':'#f5b800','Above Average':'#d94f00','Higher Priority':'#6d0000',
          'Insufficient Data':'#64706a'};

  function buildTooltipHTML(p){
    var name=window.__activeLayerName||'';
    var eligible=p.investment_eligible===true;
    var html='<div style="font-family:DM Sans,sans-serif;min-width:155px">'
      +'<b style="font-size:13px;color:#e8f0e8;display:block;margin-bottom:5px">'
      +(p.nta_name||'')+'</b>';
    if(name.indexOf('Tree Density')>=0){
      var dens=Math.round(parseFloat(p.density_2015)||0).toLocaleString();
      html+='<div style="color:#b0cbb0;font-size:11px;margin-bottom:4px">'+dens+' street trees/km²</div>'
           +'<span style="background:'+(EQ[p.equity_label]||'#888')
           +';color:#fff;padding:2px 8px;border-radius:3px;font-size:10px">'
           +(p.equity_label||'')+'</span>';
    }else if(name.indexOf('Median Household Income')>=0){
      var inc=p.median_income==null?null:parseInt(p.median_income);
      html+=inc==null
        ? '<div style="color:#b0cbb0;font-size:11px">Income estimate unavailable</div>'
        : '<div style="color:#b0cbb0;font-size:11px;margin-bottom:4px">$'+inc.toLocaleString()+' estimated median income</div>'
          +'<span style="color:#7f9582;font-size:10px">ACS ending '+(p.income_source_year||'year unavailable')+'</span>';
    }else if(name.indexOf('Screening Score')>=0){
      if(!eligible||p.underserved==null) return html+'<div style="color:#9aa59f;font-size:11px">Context only. Not ranked.</div></div>';
      var score=parseFloat(p.underserved).toFixed(3);
      html+='<div style="color:#b0cbb0;font-size:11px;margin-bottom:4px">Project screening score: '+score+'</div>'
           +'<span style="background:'+(EQ[p.equity_label]||'#888')
           +';color:#fff;padding:2px 8px;border-radius:3px;font-size:10px">'
           +(p.equity_label||'')+'</span>';
    }else if(name.indexOf('Change')>=0){
      var chg=parseInt(p.tree_change)||0;
      var cc=chg>=0?'#2fa05e':'#d94f00';
      html+='<div style="color:'+cc+';font-size:11px">'
           +(chg>=0?'+':'-')
           +Math.abs(chg).toLocaleString()+' trees since 2005</div>';
    }else if(name.indexOf('Proxy')>=0){
      if(!eligible||p.heat_proxy==null) return html+'<div style="color:#9aa59f;font-size:11px">Context only. Not ranked.</div></div>';
      var heat=parseFloat(p.heat_proxy);
      var hl=heat>=0.75?'Higher proxy':heat>=0.55?'Elevated proxy':heat>=0.35?'Middle proxy':'Lower proxy';
      var hc=heat>=0.75?'#c0392b':heat>=0.55?'#d94f00':heat>=0.35?'#f5b800':'#2fa05e';
      html+='<div style="color:#b0cbb0;font-size:11px;margin-bottom:4px">Tree + income proxy: '+heat.toFixed(3)+'</div>'
           +'<span style="color:'+hc+';font-size:10px">'+hl+'</span>';
    }else{
      html+='<span style="background:'+(EQ[p.equity_label]||'#888')
           +';color:#fff;padding:2px 8px;border-radius:3px;font-size:10px">'
           +(p.equity_label||'')+'</span>';
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
              {type:'nta_click', props:e.target.feature.properties}, '*');
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
_leg_income = (
    "<h4>Median Household Income</h4>"
    + _lr("#f2f0f7", f"&lt; ${_income_q[1]:,.0f}")
    + _lr("#cbc9e2", f"${_income_q[1]:,.0f} &#x2013; ${_income_q[2]:,.0f}")
    + _lr("#9e9ac8", f"${_income_q[2]:,.0f} &#x2013; ${_income_q[3]:,.0f}")
    + _lr("#756bb1", f"${_income_q[3]:,.0f} &#x2013; ${_income_q[4]:,.0f}")
    + _lr("#54278f", f"&gt; ${_income_q[4]:,.0f}")
)
_leg_underserved = (
    "<h4>Project Screening Score</h4>"
    + _lr("#ffffcc", f"&lt; {_underserved_q[1]:.2f} lower")
    + _lr("#fed976", f"{_underserved_q[1]:.2f} &#x2013; {_underserved_q[2]:.2f}")
    + _lr("#fd8d3c", f"{_underserved_q[2]:.2f} &#x2013; {_underserved_q[3]:.2f}")
    + _lr("#e31a1c", f"{_underserved_q[3]:.2f} &#x2013; {_underserved_q[4]:.2f}")
    + _lr("#800026", f"&gt; {_underserved_q[4]:.2f} higher")
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
    "<h4>Tree + Income Screening Proxy</h4>"
    + _lr("#ffffb2", f"&lt; {_heat_q[1]:.2f} lower")
    + _lr("#fecc5c", f"{_heat_q[1]:.2f} &#x2013; {_heat_q[2]:.2f}")
    + _lr("#fd8d3c", f"{_heat_q[2]:.2f} &#x2013; {_heat_q[3]:.2f}")
    + _lr("#f03b20", f"{_heat_q[3]:.2f} &#x2013; {_heat_q[4]:.2f}")
    + _lr("#bd0026", f"&gt; {_heat_q[4]:.2f} higher")
)

_legend_js = (
    "function updateLegend(n){"
    "['leg-density','leg-income','leg-underserved','leg-change','leg-heat']"
    ".forEach(function(id){var e=document.getElementById(id);if(e)e.style.display='none';});"
    "var s='leg-density';"
    "if(n.indexOf('Median Household Income')>=0)s='leg-income';"
    "else if(n.indexOf('Screening Score')>=0)s='leg-underserved';"
    "else if(n.indexOf('Change')>=0)s='leg-change';"
    "else if(n.indexOf('Proxy')>=0)s='leg-heat';"
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
    "<div id='leg-income' style='display:none'>" + _leg_income + "</div>"
    "<div id='leg-underserved' style='display:none'>" + _leg_underserved + "</div>"
    "<div id='leg-change' style='display:none'>" + _leg_change + "</div>"
    "<div id='leg-heat' style='display:none'>" + _leg_heat + "</div>"
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
if not live_ok:
    print(f"\n📌  DATA NOTE: Using embedded dataset.")
    print(f"    Set LIVE_DATA=True to pull live from NYC Open Data.")
